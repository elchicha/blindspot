from pathlib import Path
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestCameraManager:

    @pytest.fixture
    def mock_blink(self):
        blink = MagicMock()
        blink.urls.base_url = "https://rest-prd2.immedia-semi.com"
        return blink

    @pytest.fixture
    def mock_camera(self):
        camera = MagicMock()
        camera.name = "Street"
        camera.network_id = "298612"
        camera.camera_id = "1595650"
        camera.product_type = "sonoran"
        return camera

    @pytest.fixture
    def mock_config_response(self):
        # real data from your Street camera
        return {
            "camera": [
                {
                    "motion_sensitivity": 7,
                    "motion_alert": True,
                    "video_length": 10,
                    "video_quality": "best",
                    "illuminator_enable": 0,
                    "record_audio_enable": True,
                    "liveview_enabled": "off",
                    "motion_regions": 33554431,
                    "early_notification": True,
                    "clip_max_length": 60,
                    "snapshot_enabled": False,
                    "local_storage_enabled": False,
                    "offline_alert_count": 3,
                    "last_offline_alert": "2026-06-02T22:26:19+00:00",
                    "last_connect": {
                        "wifi_strength": -59,
                        "battery_voltage": 150,
                        "ip_address": "10.0.0.98",
                        "socket_failure_count": 3758,
                        "pir_rejections": 57128,
                    },
                }
            ],
            "signals": {
                "wifi": 4,
                "wifi_rssi": -59,
                "lfr": 5,
                "lfr_rssi": -69,
                "temp": 102,
                "battery": 3,
                "battery_state": "ok",
            },
        }

    @pytest.fixture
    def mock_homescreen(self):
        return {
            "sync_modules": [
                {
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

    async def test_get_config_returns_motion_settings(
        self, mock_blink, mock_camera, mock_config_response
    ):
        """get_config should return motion and video settings."""
        with patch(
            "blinkpy.api.http_get",
            new_callable=AsyncMock,
            return_value=mock_config_response,
        ):
            from blindspot.cameras import CameraManager

            manager = CameraManager(mock_blink)
            config = await manager.get_config(mock_camera)

        assert config["motion_sensitivity"] == 7
        assert config["motion_alert"] == True
        assert config["early_notification"] == True
        assert config["motion_regions"] == 33554431
        assert config["video_length"] == 10
        assert config["video_quality"] == "best"
        assert config["clip_max_length"] == 60
        assert config["record_audio_enable"] == True
        assert config["local_storage_enabled"] == False
        assert config["snapshot_enabled"] == False
        assert config["illuminator_enable"] == 0

    async def test_get_status_returns_hardware_state(
        self, mock_blink, mock_camera, mock_config_response
    ):
        """get_status should return wifi, battery, temp, and health metrics."""
        with patch(
            "blinkpy.api.http_get",
            new_callable=AsyncMock,
            return_value=mock_config_response,
        ):
            from blindspot.cameras import CameraManager

            manager = CameraManager(mock_blink)
            status = await manager.get_camera_status(mock_camera)

        # hardware state
        assert status["wifi_strength"] == -59  # wifi dBm
        assert status["battery_voltage"] == 150  # battery voltage
        assert status["battery_state"] == "ok"  # battery state
        assert status["temperature"] == 102  # temperature

        # health metrics
        assert status["offline_alert_count"] == 3  # offline count
        assert status["socket_failure_count"] == 3758  # socket failures
        assert status["pir_rejections"] == 57128  # pir rejections
        assert status["ip_address"] == "10.0.0.98"  # local ip

    async def test_get_sd_card_status(self, mock_blink, mock_homescreen):
        """get_sd_status should return SD card health from homescreen data."""

        with patch(
            "blinkpy.api.request_homescreen",
            new_callable=AsyncMock,
            return_value=MagicMock(json=AsyncMock(return_value=mock_homescreen)),
        ):
            from blindspot.cameras import CameraManager

            manager = CameraManager(mock_blink)
            status = await manager.get_sd_card_status()

        assert status["local_storage_status"] == "active"
        assert status["local_storage_compatible"] == False
        assert status["last_hb"] == "2026-06-25T02:01:17+00:00"

    async def test_camera_status_data(
        self, mock_blink, mock_camera, mock_config_response
    ):
        """get_camera_health should return a list of camera health dicts."""
        with patch(
            "blindspot.cameras.api.http_get",
            new_callable=AsyncMock,
            return_value=mock_config_response,
        ) as mock_http_get:
            from blindspot.cameras import CameraManager

            manager = CameraManager(mock_blink)
            camera_status_list = await manager.get_camera_status(mock_camera)

        mock_http_get.assert_awaited_once()

        assert camera_status_list["wifi_strength"] == -59
        assert camera_status_list["battery_voltage"] == 150
        assert camera_status_list["battery_state"] == "ok"
        assert camera_status_list["temperature"] == 102
