from setuptools import setup, find_namespace_packages

# Read requirements from environment.yml
def get_requirements():
    try:
        with open('environment.yml', 'r') as f:
            content = f.read()
            # Parse dependencies section of yaml
            deps_section = content.split('dependencies:')[1]
            # Get pip-specific dependencies
            pip_section = deps_section.split('- pip:')[1] if '- pip:' in deps_section else ''
            
            # Parse main conda dependencies
            conda_deps = [
                line.strip().split('=')[0] 
                for line in deps_section.split('\n') 
                if line.strip() and not line.strip().startswith('-')
            ]
            
            # Parse pip dependencies
            pip_deps = [
                line.strip().split('=')[0] 
                for line in pip_section.split('\n') 
                if line.strip() and not line.strip().startswith('-')
            ] if pip_section else []
            
            # Combine both
            return conda_deps + pip_deps
    except FileNotFoundError:
        return [
            "pymongo",
            "neo4j",
            "psycopg2",
            "web3",
            "requests",
            "eth-abi",
            "websockets",
            "fastapi",
            "uvicorn",
            # Add other known dependencies here as fallback
        ]

setup(
    name="blockchain_tracker",
    version="0.1.0",
    package_dir={"": "python"},  # This tells setuptools that packages are under python directory
    packages=find_namespace_packages(where="python"),  # This finds all packages under python/
    install_requires=get_requirements(),
    entry_points={
        "console_scripts": [
            "run-tracker=run:main",          # Main blockchain tracker
            "run-api=run_api:main",          # API server
        ]
    },
    author="Nicko G",
    python_requires=">=3.6",
)
