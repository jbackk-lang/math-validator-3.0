"""
Testy integracyjne dla pipeline_v3.py
"""

import pytest
from pipeline_v3 import process_expression

class TestPipelineV3:
    def test_pipeline_simple(self):
        """Test podstawowego przepływu."""
        result = process_expression("2 + 2")
        assert result["status"] == "SUCCESS"
        assert "filters" in result
        assert "stability" in result

    def test_pipeline_error(self):
        """Test obsługi błędów."""
        result = process_expression("2 + * 2")
        assert result["status"] == "FAILED"
        assert len(result["issues"]) > 0

    def test_pipeline_topological(self):
        """Test filtrów topologicznych."""
        result = process_expression(
            "1/(x-1)",
            options={"topological": True}
        )
        assert "singularity" in result["filters"]
        assert result["filters"]["singularity"]["status"] in ["PASSED", "FAILED"]
