import asyncio
import logging
from src.blindspot.auth import SessionManager
from src.blindspot.dashboard import MaintenanceDashboard, render_dashboard
from src.blindspot.network_diagnostics import check_port

logging.basicConfig(level=logging.ERROR)


async def main():
    print("Connecting to Blink...")
    manager = SessionManager(creds_file="config/blink_creds.json")
    blink = await manager.login()

    # dashboard
    dashboard = MaintenanceDashboard(blink)
    result = await dashboard.get_dashboard()
    render_dashboard(result)

    # network port check
    camera_ips = [
        (c["ip_address"], 443) for c in result["cameras"] if c.get("ip_address")
    ]
    endpoints = [
        ("rest-prd2.immedia-semi.com", 443),
        ("api.oauth.blink.com", 443),
    ] + camera_ips

    print("\nNETWORK PORT CHECK")
    print("=" * 50)
    for host, port in endpoints:
        port_result = check_port(host, port)
        icon = "✅" if port_result["success"] else "❌"
        duration = f"{port_result['duration_ms']:.1f}ms"
        error = f" — {port_result['error']}" if port_result["error"] else ""
        print(f"{icon} {host}:{port} ({duration}){error}")

    await blink.auth.session.close()


asyncio.run(main())
