from blinkpy import api


class SyncModuleManager:

    def __init__(self, blink):
        self.blink = blink

    async def get_sync_module_status(self):
        response = await api.request_homescreen(self.blink)
        data = await response.json()

        status = []
        for sync_module in data["sync_modules"]:
            status.append({
                "name": sync_module.get("name"),
            })
        return status