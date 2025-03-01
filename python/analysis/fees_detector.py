import psycopg2
import pandas as pd
import numpy as np
from decimal import Decimal, getcontext
from collections import defaultdict
import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import os
from database.sql.base import SQLDatabase
from database import MongoDatabase
from database.operator import DatabaseOperator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('factory_fee_analysis.log'),
        logging.StreamHandler()
    ]
)

# Set precision for decimal calculations
getcontext().prec = 36

def calculate_fee_for_pool(db: SQLDatabase, chain, contract_address, sample_size=30):
    """
    Calculate exact fee percentage for a single pool using swap and sync events
    
    Args:
        db: Database connection
        chain: Blockchain network (e.g., 'base')
        contract_address: Pool contract address
        sample_size: Number of swaps to analyze
    
    Returns:
        Dict with fee calculation results or None if calculation fails
    """
    try:
        logging.info(f"Calculating fee for pool {contract_address}")
        
        # Modified query to get syncs before each swap
        query = """
        WITH swap_syncs AS (
            -- Get all swaps with their preceding sync
            SELECT 
                s.transaction_hash,
                s.log_index,
                s.timestamp,
                s.amount0,
                s.amount1,
                (
                    SELECT sync.reserve0
                    FROM evm_syncs sync
                    WHERE sync.chain = s.chain 
                    AND sync.contract_address = s.contract_address
                    AND sync.timestamp <= s.timestamp
                    ORDER BY sync.timestamp DESC, sync.log_index DESC
                    LIMIT 1
                ) as reserve0,
                (
                    SELECT sync.reserve1
                    FROM evm_syncs sync
                    WHERE sync.chain = s.chain 
                    AND sync.contract_address = s.contract_address
                    AND sync.timestamp <= s.timestamp
                    ORDER BY sync.timestamp DESC, sync.log_index DESC
                    LIMIT 1
                ) as reserve1,
                s.token0_address,
                s.token1_address
            FROM evm_swaps s
            WHERE s.chain = %s 
            AND s.contract_address = %s
            ORDER BY s.timestamp DESC
            LIMIT %s
        )
        SELECT * FROM swap_syncs 
        WHERE reserve0 IS NOT NULL 
        AND reserve1 IS NOT NULL;
        """
        
        conn = db.get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(query, (chain, contract_address, sample_size * 2))  # Get more swaps to account for filtering
                columns = [desc[0] for desc in cur.description]
                events = pd.DataFrame(cur.fetchall(), columns=columns)
                logging.info(f"Found {len(events)} valid swaps with reserves for pool {contract_address}")
        finally:
            db.return_connection(conn)
        
        if events.empty:
            logging.warning(f"No valid swaps with reserves found for pool {contract_address}")
            return None
            
        # Process each swap
        fees = []
        for _, event in events.iterrows():
            try:
                amount0 = Decimal(str(event['amount0']))
                amount1 = Decimal(str(event['amount1']))
                reserve0 = Decimal(str(event['reserve0']))
                reserve1 = Decimal(str(event['reserve1']))
                
                # Log the values for debugging
                logging.info(f"Processing swap: amount0={amount0}, amount1={amount1}, reserve0={reserve0}, reserve1={reserve1}")
                
                # Determine swap direction
                if amount0 > 0 and amount1 < 0:  # Token0 in, Token1 out
                    amount_in = amount0
                    amount_out = abs(amount1)
                    reserve_in = reserve0
                    reserve_out = reserve1
                    logging.info(f"Token0 to Token1 swap: in={amount_in}, out={amount_out}, reserve_in={reserve_in}, reserve_out={reserve_out}")
                elif amount0 < 0 and amount1 > 0:  # Token1 in, Token0 out
                    amount_in = amount1
                    amount_out = abs(amount0)
                    reserve_in = reserve1
                    reserve_out = reserve0
                    logging.info(f"Token1 to Token0 swap: in={amount_in}, out={amount_out}, reserve_in={reserve_in}, reserve_out={reserve_out}")
                else:
                    logging.info(f"Skipping invalid swap direction: amount0={amount0}, amount1={amount1}")
                    continue
                
                # Skip invalid or complex swaps
                if amount_in <= 0 or amount_out <= 0 or reserve_in <= 0 or reserve_out <= 0:
                    logging.info("Skipping swap with invalid amounts or reserves")
                    continue
                    
                # Calculate theoretical output with NO fee
                k = reserve_in * reserve_out
                theoretical_out_no_fee = reserve_out - k / (reserve_in + amount_in)
                
                # Calculate fee percentage (taking absolute value)
                fee_amount = abs(theoretical_out_no_fee - amount_out)
                fee_percentage = fee_amount / theoretical_out_no_fee
                
                logging.info(f"Fee calculation: theoretical_out={theoretical_out_no_fee}, actual_out={amount_out}, fee_percentage={fee_percentage}")
                
                # Only add reasonable fees (between 0% and 5%)
                if 0 < fee_percentage < 0.05:
                    fees.append(float(fee_percentage))
                    logging.info(f"Valid fee found: {fee_percentage:.4%}")
                else:
                    logging.info(f"Fee outside valid range: {fee_percentage:.4%}")
                    
            except Exception as e:
                logging.error(f"Error processing swap: {str(e)}")
                continue
        
        if not fees:
            logging.warning(f"No valid fees calculated for pool {contract_address}")
            return None
            
        # Calculate median fee
        median_fee = np.median(fees)
        std_dev = np.std(fees)
        
        result = {
            "fee_decimal": median_fee,
            "fee_bps": int(round(median_fee * 10000)),
            "sample_size": len(fees),
            "std_dev": std_dev
        }
        
        logging.info(f"Successfully calculated fee for pool {contract_address}: {result['fee_bps']} bps")
        return result
    
    except Exception as e:
        logging.error(f"Error calculating fee for pool {contract_address}: {str(e)}")
        return None


def analyze_factory_fees(db_operator: DatabaseOperator, chain, factory_address=None, max_pools_per_factory=10, 
                         parallel=True, max_workers=4):
    """
    Analyze fees across all pools from a factory (or all factories if none specified)
    
    Args:
        db_operator: Database operator
        chain: Blockchain network (e.g., 'base')
        factory_address: Optional specific factory to analyze
        max_pools_per_factory: Maximum number of pools to check per factory
        parallel: Whether to use parallel processing
        max_workers: Number of worker threads if parallel is True
        
    Returns:
        Dict with factory fee analysis results
    """
    start_time = time.time()
    
    # Create results directory with absolute path
    results_dir = os.path.abspath("fee_results")
    os.makedirs(results_dir, exist_ok=True)
    logging.info(f"Saving results to directory: {results_dir}")
    
    # Create a timestamp for this analysis run
    run_timestamp = time.strftime('%Y%m%d_%H%M%S')
    results_file = os.path.join(results_dir, f"{chain}_factory_fees_{run_timestamp}.json")
    logging.info(f"Results will be saved to: {results_file}")
    
    try:
        # 1. Get factories to analyze using SQL connection
        if factory_address:
            factory_query = """
            SELECT DISTINCT factory_address 
            FROM evm_swaps 
            WHERE chain = %s AND factory_address = %s
            """
            params = (chain, factory_address)
        else:
            factory_query = """
            SELECT DISTINCT factory_address 
            FROM evm_swaps 
            WHERE chain = %s AND factory_address IS NOT NULL
            """
            params = (chain,)
        
        conn = db_operator.sql.db.get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(factory_query, params)
                factories = [row[0] for row in cur.fetchall()]
        finally:
            db_operator.sql.db.return_connection(conn)
        
        if not factories:
            logging.warning("No factories found to analyze")
            return {"status": "error", "message": "No factories found"}
        
        logging.info(f"Analyzing {len(factories)} factories on {chain}")
        results = {}
        
        # Load existing results if file exists
        if os.path.exists(results_file):
            logging.info(f"Loading existing results from {results_file}")
            with open(results_file, 'r') as f:
                results = json.load(f)
        
        # 2. Process each factory
        for idx, factory in enumerate(factories, 1):
            logging.info(f"Processing factory {idx}/{len(factories)}: {factory}")
            
            if factory in results:
                logging.info(f"Skipping already analyzed factory {factory}")
                continue
            
            # Get pools for this factory
            pool_query = """
            SELECT DISTINCT contract_address
            FROM evm_swaps
            WHERE chain = %s AND factory_address = %s
            LIMIT %s
            """
            
            conn = db_operator.sql.db.get_connection()
            try:
                with conn.cursor() as cur:
                    cur.execute(pool_query, (chain, factory, max_pools_per_factory))
                    pools = [row[0] for row in cur.fetchall()]
            finally:
                db_operator.sql.db.return_connection(conn)
            
            if not pools:
                continue
            
            logging.info(f"Analyzing {len(pools)} pools for factory {factory}")
            
            # Calculate fees for each pool (in parallel or sequentially)
            pool_fees = []
            
            if parallel and len(pools) > 1:
                # Use thread pool for parallel processing
                with ThreadPoolExecutor(max_workers=max_workers) as executor:
                    # Submit all pool calculations
                    future_to_pool = {
                        executor.submit(calculate_fee_for_pool, db_operator.sql.db, chain, pool): pool 
                        for pool in pools
                    }
                    
                    # Collect results as they complete
                    for future in as_completed(future_to_pool):
                        pool = future_to_pool[future]
                        try:
                            fee_result = future.result()
                            if fee_result:
                                pool_fees.append(fee_result)
                        except Exception as e:
                            logging.error(f"Error processing pool {pool}: {str(e)}")
            else:
                # Process sequentially
                for pool in pools:
                    fee_result = calculate_fee_for_pool(db_operator.sql.db, chain, pool)
                    if fee_result:
                        pool_fees.append(fee_result)
            
            # Analyze results for this factory
            if pool_fees:
                # Extract fee values
                fee_values = [result['fee_decimal'] for result in pool_fees]
                
                # Calculate statistics
                median_fee = np.median(fee_values)
                mean_fee = np.mean(fee_values)
                std_dev = np.std(fee_values)
                
                # Check for consistency (all pools should have the same fee)
                fee_counts = {}
                for fee in fee_values:
                    # Round to nearest basis point (0.01%)
                    rounded_fee = round(fee * 10000) / 10000
                    if rounded_fee in fee_counts:
                        fee_counts[rounded_fee] += 1
                    else:
                        fee_counts[rounded_fee] = 1
                
                # Find most common fee
                most_common_fee = max(fee_counts, key=fee_counts.get)
                consistency = fee_counts[most_common_fee] / len(fee_values)
                
                # Common fee representations
                fee_bps = int(round(most_common_fee * 10000))
                fee_percentage = most_common_fee * 100
                
                # Find fraction representation
                fraction = None
                for denominator in [100, 1000, 10000]:
                    numerator = round((1 - most_common_fee) * denominator)
                    reconstructed_fee = 1 - (numerator / denominator)
                    if abs(reconstructed_fee - most_common_fee) < 0.0001:
                        fraction = f"{numerator}/{denominator}"
                        break
                
                results[factory] = {
                    "factory_address": factory,
                    "chain": chain,
                    "fee_data": {
                        "median_fee_decimal": float(median_fee),  # Convert Decimal to float for JSON
                        "median_fee_percentage": float(median_fee * 100),
                        "median_fee_bps": int(round(median_fee * 10000)),
                        "most_common_fee_decimal": float(most_common_fee),
                        "most_common_fee_percentage": float(most_common_fee * 100),
                        "most_common_fee_bps": fee_bps,
                        "fee_fraction": fraction,
                        "consistency": float(consistency),
                        "std_dev": float(std_dev)
                    },
                    "analysis_stats": {
                        "pools_analyzed": len(pool_fees),
                        "total_swaps_analyzed": sum(p['sample_size'] for p in pool_fees),
                        "confidence": "High" if consistency > 0.9 and len(pool_fees) >= 3 else "Medium"
                    },
                    "timestamp": time.strftime('%Y-%m-%d %H:%M:%S')
                }
                
                # Save results after each factory
                try:
                    with open(results_file, 'w') as f:
                        json.dump(results, f, indent=2)
                    logging.info(f"Successfully saved results for factory {factory} to {results_file}")
                except Exception as e:
                    logging.error(f"Error saving results for factory {factory}: {str(e)}")
            else:
                logging.warning(f"No pool fees calculated for factory {factory}")
        
        # Final results processing
        factory_fees = {
            factory: result["fee_data"]["most_common_fee_bps"] * 100 
            if result["analysis_stats"]["confidence"] == "High"
            else result["fee_data"]["median_fee_bps"] * 100
            for factory, result in results.items()
        }
        
        execution_time = time.time() - start_time
        
        return {
            "status": "success",
            "chain": chain,
            "factories_analyzed": len(results),
            "factory_results": results,
            "factory_fees": factory_fees,
            "execution_time_seconds": execution_time,
            "results_file": results_file
        }
    
    except Exception as e:
        logging.error(f"Error in factory fee analysis: {str(e)}")
        return {"status": "error", "message": str(e)}


def write_fees_to_file(factory_fees, chain, output_dir="fee_results"):
    """
    Write factory fees to a text file
    
    Args:
        factory_fees: Dict of factory_address -> fee
        chain: Blockchain network
        output_dir: Directory to write results
    
    Returns:
        Path to the output file
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate filename with timestamp
    timestamp = time.strftime('%Y%m%d_%H%M%S')
    filename = f"{chain}_factory_fees_{timestamp}.txt"
    filepath = os.path.join(output_dir, filename)
    
    # Write fees to file
    with open(filepath, 'w') as f:
        f.write(f"# {chain.upper()} Factory Fees\n")
        f.write(f"# Generated on: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"# Total factories: {len(factory_fees)}\n\n")
        f.write("factory_address,fee_int\n")
        
        # Sort by factory address for consistency
        for factory in sorted(factory_fees.keys()):
            fee = factory_fees[factory]
            f.write(f"{factory},{int(fee)}\n")
    
    logging.info(f"Factory fees written to {filepath}")
    return filepath


def main():
    try:
        # Initialize SQL database first
        sql_db = SQLDatabase()
        mongo_db = MongoDatabase()
        
        # Initialize database operator with the SQLDatabase instance
        db_operator = DatabaseOperator(
            sql_db=sql_db,  # Pass the SQLDatabase instance, not a string
            mongo_db=mongo_db
        )
        
        # Specify chain to analyze
        chain = "base"
        
        # Analyze all factories on the chain
        result = analyze_factory_fees(
            db_operator=db_operator,
            chain=chain,
            factory_address=None,
            max_pools_per_factory=10,
            parallel=True,
            max_workers=4
        )
        
        if result and result.get("status") == "success":
            # Write results to files
            output_file = write_fees_to_file(result["factory_fees"], chain)
            logging.info(f"Analysis complete. Analyzed {result['factories_analyzed']} factories.")
            logging.info(f"Results written to {output_file}")
            
            # Save detailed JSON results
            json_file = os.path.join(
                "fee_results", 
                f"{chain}_factory_fee_details_{time.strftime('%Y%m%d_%H%M%S')}.json"
            )
            
            # Clean results for JSON serialization
            clean_results = {}
            if 'factory_results' in result:
                for factory, data in result['factory_results'].items():
                    clean_results[factory] = json.loads(
                        json.dumps(data, default=lambda x: float(x) if isinstance(x, Decimal) else x)
                    )
                
                with open(json_file, 'w') as f:
                    json.dump(clean_results, f, indent=2)
                    
                logging.info(f"Detailed results written to {json_file}")
        else:
            logging.error(f"Analysis failed: {result.get('message') if result else 'No result returned'}")
    
    except Exception as e:
        logging.error(f"Error in main execution: {str(e)}")
        raise


if __name__ == "__main__":
    main()