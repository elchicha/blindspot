import os

os.environ["SSLKEYLOGFILE"] = "/tmp/blink_keys.log"

import asyncio
import logging
from src.blindspot.auth import SessionManager
from src.blindspot.cameras import CameraManager
from src.blindspot.network_diagnostics import check_port

from blinkpy import api

logging.basicConfig(level=logging.ERROR)


async def main():
    print("Connecting to Blink...")
    manager = SessionManager(creds_file="config/blink_creds.json")
    blink = await manager.login()

    cameras = CameraManager(blink)
    camera_statuses = []  # collect as you go

    print(f"\nFound {len(blink.cameras)} cameras:\n")

    for name, camera in blink.cameras.items():
        config = await cameras.get_config(camera)
        cam_status = await cameras.get_camera_status(camera)
        camera_statuses.append(cam_status)  # collect here

        print(f"\n{name}:")
        print(f"  Status             : {cam_status['status']}")
        print(f"  Motion sensitivity : {config['motion_sensitivity']}")
        print(f"  Video quality      : {config['video_quality']}")
        print(f"  Night vision       : {config['illuminator_enable']}")
        print(f"  WiFi               : {cam_status['wifi_strength']} dBm")
        print(
            f"  Battery            : {cam_status['battery_state']} ({cam_status['battery_voltage']}v)"
        )
        print(f"  Battery Drain Rate : {cam_status['battery_drain_rate']}")
        print(f"  Temperature        : {cam_status['temperature']}°F")
        print(f"  IP                 : {cam_status['ip_address']}")
        print(f"  PIR rejections     : {cam_status['pir_rejections']}")
        print(f"  Offline count      : {cam_status['offline_alert_count']}")
        print(f"  Last Connected     : {cam_status['last_connect_at']}")

    endpoints = [
        ("rest-prd2.immedia-semi.com", 443),
        ("api.oauth.blink.com", 443),
    ]
    camera_ips = [
        (s["ip_address"], 443) for s in camera_statuses if s and s["ip_address"]
    ]

    all_endpoints = endpoints + camera_ips

    print("\nNETWORK PORT CHECK")
    print("=" * 50)
    for host, port in all_endpoints:
        port_result = check_port(host, port)
        icon = "✅" if port_result["success"] else "❌"
        duration = f"{port_result['duration_ms']:.1f}ms"
        error = f" — {port_result['error']}" if port_result["error"] else ""
        print(f"{icon} {host}:{port} ({duration}){error}")

    await blink.auth.session.close()


asyncio.run(main())
