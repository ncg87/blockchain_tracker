use tokio_postgres::{Client, NoTls, Error};
use serde::{Serialize, Deserialize};

#[derive(Debug)]
pub struct SQLDatabase {
    client: Client,
}

impl SQLDatabase {
    pub async fn new(connection_string: &str) -> Result<Self, Error> {
        let (client, connection) = tokio_postgres::connect(connection_string, NoTls).await?;
        
        // Spawn the connection handler to run in the background
        tokio::spawn(async move {
            if let Err(e) = connection.await {
                eprintln!("Connection error: {}", e);
            }
        });

        Ok(SQLDatabase { client })
    }

    pub async fn fetch_blocks(&self, last_block: Option<i64>, limit: i32) -> Result<Vec<(String, i64, i64)>, Error> {
        let query = "
            SELECT network, block_number, timestamp 
            FROM blocks 
            WHERE network IN ('Ethereum', 'Base', 'BNB')
            AND block_number < $1
            ORDER BY block_number DESC
            LIMIT $2
        ";

        let last_block = last_block.unwrap_or(i64::MAX);
        let rows = self.client.query(query, &[&last_block, &limit]).await?;

        let blocks = rows.iter().map(|row| {
            let network: String = row.get(0);
            let block_number: i64 = row.get(1);
            let timestamp: i64 = row.get(2);
            (network, block_number, timestamp)
        }).collect();

        Ok(blocks)
    }
}

use pyo3::prelude::*;
mod db_operations;

#[pymodule]
fn rust_db_ops(_py: Python, m: &PyModule) -> PyResult<()> {
    #[pyclass]
    struct RustSQLDatabase {
        inner: db_operations::SQLDatabase,
    }

    #[pymethods]
    impl RustSQLDatabase {
        #[new]
        fn new(connection_string: &str) -> PyResult<Self> {
            let rt = tokio::runtime::Runtime::new().unwrap();
            let inner = rt.block_on(db_operations::SQLDatabase::new(connection_string))
                .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;
            Ok(RustSQLDatabase { inner })
        }

        fn fetch_blocks(&self, last_block: Option<i64>, limit: i32) -> PyResult<Vec<(String, i64, i64)>> {
            let rt = tokio::runtime::Runtime::new().unwrap();
            rt.block_on(self.inner.fetch_blocks(last_block, limit))
                .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))
        }
    }

    m.add_class::<RustSQLDatabase>()?;
    Ok(())
}