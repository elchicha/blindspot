from blinkpy import api


class SyncModuleManager:
    SYNC_MODULES_KEY = "sync_modules"

    def __init__(self, blink):
        self.blink = blink

    async def get_sync_module_status(self):
        response = await api.request_homescreen(self.blink)
        homescreen_data = await response.json()
        sync_module = homescreen_data[self.SYNC_MODULES_KEY][0]

        return {
            "name": sync_module.get("name"),
            "status": sync_module.get("status"),
            "local_storage_enabled": sync_module.get("local_storage_enabled"),
            "local_storage_status": sync_module.get("local_storage_status"),
            "last_backup": sync_module.get("last_hb"),
            "wifi_strength": sync_module.get("wifi_strength"),
        }
