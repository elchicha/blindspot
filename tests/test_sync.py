from unittest.mock import MagicMock, AsyncMock, patch

import pytest


class TestSyncModuleManager:
    @pytest.fixture
    def mock_blink(self):
        blink = MagicMock()
        blink.urls.base_url = "https://rest-prd2.immedia-semi.com"
        return blink

    @pytest.fixture
    def mock_homescreen(self):
        return {
            "sync_modules": [
                {
                    "name": "My Blink Sync Module",
                    "status": "online",
                    "local_storage_enabled": True,
                    "local_storage_compatible": False,
                    "local_storage_status": "active",
                    "last_hb": "2026-06-25T02:01:17+00:00",
                    "wifi_strength": 5,
                }
            ],
            "cameras": [
                {
                    "name": "Street",
                    "status": "offline",
                    "battery": "low",
                    "signals": {"wifi": 1, "battery": 3, "temp": 96},
                },
                {
                    "name": "Tree",
                    "status": "done",
                    "battery": "ok",
                    "signals": {"wifi": 4, "battery": 3, "temp": 68},
                },
            ],
        }

    async def test_get_sync_module_status_returns_dict(
        self, mock_blink, mock_homescreen
    ):
        """get_sync_module_status should return Sync Module status, wifi, storage status."""

        with patch(
            "blinkpy.api.request_homescreen",
            new_callable=AsyncMock,
            return_value=MagicMock(json=AsyncMock(return_value=mock_homescreen)),
        ):
            from blindspot.sync import SyncModuleManager

            manager = SyncModuleManager(mock_blink)
            sync_module_status = await manager.get_sync_module_status()

            assert len(sync_module_status) == 6
