# python/run_api.py
import os
import sys
import uvicorn

# Add the python directory to PYTHONPATH
PYTHON_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(PYTHON_DIR)

if __name__ == "__main__":
    uvicorn.run("api.main:app", host="localhost", port=8000, reload=True)