import pytest
from chains.base_models import BasePipeline

def test_base_pipeline_initialization(test_db):
    """Test base pipeline initialization."""
    class TestPipeline(BasePipeline):
        async def run(self, *args, **kwargs):
            pass
        async def run_historical(self, *args, **kwargs):
            pass

    pipeline = TestPipeline(test_db, "Test")
    assert pipeline.database == test_db
    assert pipeline.chain_name == "Test"
    assert pipeline.logger is not None