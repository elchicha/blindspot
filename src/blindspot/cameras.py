import logging
from blinkpy import api

_LOGGER = logging.getLogger(__name__)


class CameraManager:

    def __init__(self, blink):
        self.blink = blink

    async def _fetch_raw(self, camera):
        url = (
            f"{self.blink.urls.base_url}"
            f"/network/{camera.network_id}"
            f"/camera/{camera.camera_id}/config"
        )
        return await api.http_get(self.blink, url)

    async def get_config(self, camera):
        raw = await self._fetch_raw(camera)

        if not raw:
            return None

        cam = raw["camera"][0]

        return {
            "motion_sensitivity": cam.get("motion_sensitivity"),
            "motion_alert": cam.get("motion_alert"),
            "early_notification": cam.get("early_notification"),
            "motion_regions": cam.get("motion_regions"),
            "video_length": cam.get("video_length"),
            "video_quality": cam.get("video_quality"),
            "clip_max_length": cam.get("clip_max_length"),
            "record_audio_enable": cam.get("record_audio_enable"),
            "local_storage_enabled": cam.get("local_storage_enabled"),
            "snapshot_enabled": cam.get("snapshot_enabled"),
            "illuminator_enable": cam.get("illuminator_enable"),
        }

    async def get_camera_status(self, camera):
        raw = await self._fetch_raw(camera)
        if not raw:
            return None

        cam = raw["camera"][0]
        signals = raw["signals"]
        last_connect = cam.get("last_connect", {})

        return {
            "wifi_strength": signals.get("wifi_rssi"),
            "battery_voltage": last_connect.get("battery_voltage"),
            "battery_state": signals.get("battery_state"),
            "temperature": signals.get("temp"),
            "offline_alert_count": cam.get("offline_alert_count"),
            "last_offline_alert": cam.get("last_offline_alert"),
            "socket_failure_count": last_connect.get("socket_failure_count"),
            "pir_rejections": last_connect.get("pir_rejections"),
            "ip_address": last_connect.get("ip_address"),
        }

    async def get_sd_card_status(self):
        response = await api.request_homescreen(self.blink)
        data = await response.json()

        sync = data["sync_modules"][0]

        return {
            "local_storage_status": sync.get("local_storage_status"),
            "local_storage_compatible": sync.get("local_storage_compatible"),
            "last_hb": sync.get("last_hb"),
        }
