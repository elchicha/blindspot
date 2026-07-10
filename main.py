import asyncio
import logging
from src.blindspot.auth import SessionManager
from src.blindspot.cameras import CameraManager

from blinkpy import api

logging.basicConfig(level=logging.ERROR)


async def main():
    print("Connecting to Blink...")
    manager = SessionManager(creds_file="config/blink_creds.json")
    blink = await manager.login()

    cameras = CameraManager(blink)

    print(f"\nFound {len(blink.cameras)} cameras:\n")

    for name, camera in blink.cameras.items():
        config = await cameras.get_config(camera)
        status = await cameras.get_camera_status(camera)
        print(f"\n{name}:")
        print(f"  Status             : {status['status']}")
        print(f"  Motion sensitivity : {config['motion_sensitivity']}")
        print(f"  Video quality      : {config['video_quality']}")
        print(f"  Night vision       : {config['illuminator_enable']}")
        print(f"  WiFi               : {status['wifi_strength']} dBm")
        print(
            f"  Battery            : {status['battery_state']} ({status['battery_voltage']}v)"
        )
        print(f"  Battery Drain Rate : {status['battery_drain_rate']}")
        print(f"  Temperature        : {status['temperature']}°F")
        print(f"  IP                 : {status['ip_address']}")
        print(f"  PIR rejections     : {status['pir_rejections']}")
        print(f"  Offline count      : {status['offline_alert_count']}")
        print(f"  Last Connected     : {status['last_connect_at']}")

    await blink.auth.session.close()


asyncio.run(main())
