import pytest
from chains.base_models import BaseProcessor

def test_base_processor_initialization(test_db):
    """Test base processor initialization."""
    processor = BaseProcessor(test_db, "Test")
    assert processor.network == "Test"
    assert processor.logger is not None
    assert processor.insert_ops is not None
    assert processor.query_ops is not None