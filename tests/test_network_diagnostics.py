import pytest
from unittest.mock import patch, MagicMock


class TestCheckPort:

    @pytest.fixture
    def open_port_result(self):
        return {
            "success": True,
            "host": "rest-prd2.immedia-semi.com",
            "port": 443,
            "duration_ms": 45.3,
            "error": None,
        }

    def test_check_port_open(self, open_port_result):
        """Port 443 on Blink module should be reachable."""
        with patch(
            "blindspot.network_diagnostics.socket.create_connection"
        ) as mock_connect:
            mock_connect.return_value.__enter__ = MagicMock(return_value=MagicMock())
            from blindspot.network_diagnostics import check_port

            result = check_port("rest-prd2.immedia-semi.com", 443)

        assert result["success"] == True
        assert result["host"] == "rest-prd2.immedia-semi.com"
        assert result["port"] == 443
        assert result["duration_ms"] >= 0

    def test_check_port_returns_duration(self):
        pass
