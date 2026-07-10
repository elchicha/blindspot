import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestMaintenanceDashboard:
    @pytest.fixture
    def mock_blink(self):
        return MagicMock()

    @pytest.fixture
    def mock_camera_statuses(self):
        return [
            {
                "name": "Street",
                "status": "offline",
                "battery": "low",
                "wifi_strength": 1,
                "temperature": 96,
            },
            {
                "name": "Tree",
                "status": "done",
                "battery": "ok",
                "wifi_strength": 4,
                "temperature": 68,
            },
        ]

    @pytest.fixture
    def mock_sync_module_status(self):
        return {
            "name": "My Blink Sync Module",
            "status": "online",
            "local_storage_enabled": True,
            "local_storage_status": "active",
            "last_backup": "2026-06-25T02:01:17+00:00",
            "wifi_strength": 5,
        }

    async def test_get_dashboard_returns_current_camera_and_sync_status(
        self, mock_blink, mock_camera_statuses, mock_sync_module_status
    ):
        with (
            patch("blindspot.dashboard.CameraManager") as MockCameraManager,
            patch("blindspot.dashboard.SyncModuleManager") as MockSyncModuleManager,
        ):
            MockCameraManager.return_value.get_camera_status = AsyncMock(
                return_value=mock_camera_statuses
            )
            MockSyncModuleManager.return_value.get_sync_module_status = AsyncMock(
                return_value=mock_sync_module_status
            )

            from blindspot.dashboard import MaintenanceDashboard

            dashboard = MaintenanceDashboard(mock_blink)
            result = await dashboard.get_dashboard()

        assert result["overall_health"] == "healthy"


class TestEvaluateCameraHealth:

    @pytest.fixture
    def healthy_camera(self):
        return {
            "name": "Door",
            "status": "done",
            "battery_state": "ok",
            "wifi_strength": -45,
            "last_connect_at": "2026-07-10T04:00:00+00:00",
        }

    @pytest.fixture
    def critical_camera(self):
        return {
            "name": "Street",
            "status": "offline",
            "battery_state": "low",
            "wifi_strength": -72,
            "last_connect_at": "2026-07-10T04:00:00+00:00",
        }

    @pytest.fixture
    def needs_attention_camera(self):
        return {
            "name": "Tree",
            "status": "done",
            "battery_state": "ok",
            "wifi_strength": -63,
            "last_connect_at": "2026-06-10T04:00:00+00:00",
        }

    def test_evaluate_camera_health_healthy(self, healthy_camera):
        from blindspot.dashboard import evaluate_camera_health

        result = evaluate_camera_health(healthy_camera)
        assert result["level"] == "healthy"
        assert result["issues"] == []

    def test_evaluate_camera_health_critical(self, critical_camera):
        from blindspot.dashboard import evaluate_camera_health

        result = evaluate_camera_health(critical_camera)

        assert result["level"] == "critical"
        assert "camera is offline" in result["issues"]
        assert "battery is low" in result["issues"]

    def test_evaluate_camera_health_needs_attention(self, needs_attention_camera):
        from blindspot.dashboard import evaluate_camera_health

        result = evaluate_camera_health(needs_attention_camera)

        assert result["level"] == "needs_attention"
        assert "camera has not checked in recently" in result["issues"]
