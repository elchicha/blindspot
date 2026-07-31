from datetime import datetime, timezone

from .cameras import CameraManager
from .sync import SyncModuleManager

CRITICAL_LEVEL = "critical"
NEEDS_ATTENTION_LEVEL = "needs_attention"
HEALTHY_LEVEL = "healthy"

OFFLINE_STATUS = "offline"
LOW_BATTERY_STATE = "low"
STALE_CHECK_IN_THRESHOLD_HOURS = 24

ISSUE_CAMERA_OFFLINE = "camera is offline"
ISSUE_BATTERY_LOW = "battery is low"
ISSUE_NOT_CHECKED_IN = "camera has not checked in recently"

ISSUE_SYNC_MODULE_OFFLINE = "sync module is offline"
ISSUE_SD_CARD_NOT_ACTIVE = "SD card is not active"
ISSUE_SYNC_MODULE_WIFI_WEAK = "sync module wifi signal is weak"


CRITICAL_ISSUES = {ISSUE_CAMERA_OFFLINE, ISSUE_BATTERY_LOW, ISSUE_SYNC_MODULE_OFFLINE}


def _get_recent_check_in_issue(camera):
    last_connected_at = camera.get("last_connect_at")
    if not last_connected_at:
        return None

    last_connected = datetime.fromisoformat(last_connected_at)
    current_time = datetime.now(tz=timezone.utc)
    hours_since_last_connection = (current_time - last_connected).total_seconds() / 3600

    if hours_since_last_connection > STALE_CHECK_IN_THRESHOLD_HOURS:
        return ISSUE_NOT_CHECKED_IN

    return None


def _determine_health_level(issues):
    if CRITICAL_ISSUES.intersection(issues):
        return CRITICAL_LEVEL

    if issues:
        return NEEDS_ATTENTION_LEVEL

    return HEALTHY_LEVEL


def _get_recommendations(issues, camera):
    recommendations = []

    if ISSUE_CAMERA_OFFLINE in issues:
        recommendations.append("Check battery level and replace if needed")

    if ISSUE_BATTERY_LOW in issues:
        recommendations.append("Replace batteries immediately")

    if ISSUE_NOT_CHECKED_IN in issues:
        if camera.get("status") == "offline":
            recommendations.append("Camera is offline — check power and WiFi signal")
        else:
            recommendations.append(
                "Camera online but not syncing — restart sync module or move it closer"
            )

    return recommendations


def evaluate_camera_health(camera):

    issues = []

    camera_status = camera.get("status")
    battery_state = camera.get("battery_state")

    if camera_status == OFFLINE_STATUS:
        issues.append(ISSUE_CAMERA_OFFLINE)

    if battery_state == LOW_BATTERY_STATE:
        issues.append(ISSUE_BATTERY_LOW)

    check_in_issue = _get_recent_check_in_issue(camera)
    if check_in_issue:
        issues.append(check_in_issue)

    return {
        "level": _determine_health_level(issues),
        "issues": issues,
        "recommendations": _get_recommendations(issues, camera),
    }


def evaluate_sync_module_health(sync_module):
    issues = []
    sync_module_status = sync_module.get("status")
    local_storage_status = sync_module.get("local_storage_status")
    wifi_strength = sync_module.get("wifi_strength")

    if sync_module_status == "offline":
        issues.append(ISSUE_SYNC_MODULE_OFFLINE)

    if local_storage_status != "active":
        issues.append(ISSUE_SD_CARD_NOT_ACTIVE)

    if wifi_strength is not None and wifi_strength <= 2:
        issues.append(ISSUE_SYNC_MODULE_WIFI_WEAK)

    return {"level": _determine_health_level(issues), "issues": issues}


def _evaluate_overall_health(camera_statuses, sync_module_status):
    critical_cameras = []
    needs_attention_cameras = []

    # evaluate each camera
    for camera in camera_statuses:
        health = evaluate_camera_health(camera)
        if health["level"] == CRITICAL_LEVEL:
            critical_cameras.append(camera["name"])
        elif health["level"] == NEEDS_ATTENTION_LEVEL:
            needs_attention_cameras.append(camera["name"])

    # evaluate sync module
    sync_health = evaluate_sync_module_health(sync_module_status)

    # determine overall level
    if sync_health["level"] == CRITICAL_LEVEL or critical_cameras:
        overall_level = CRITICAL_LEVEL
    elif sync_health["level"] == NEEDS_ATTENTION_LEVEL or needs_attention_cameras:
        overall_level = NEEDS_ATTENTION_LEVEL
    else:
        overall_level = HEALTHY_LEVEL

    summary = f"{len(critical_cameras)} critical, {len(needs_attention_cameras)} need attention"
    if sync_health["level"] == CRITICAL_LEVEL:
        summary += " — SYNC MODULE OFFLINE"

    return {
        "level": overall_level,
        "critical_cameras": critical_cameras,
        "needs_attention_cameras": needs_attention_cameras,
        "sync_module_level": sync_health["level"],
        "summary": summary,
    }


def render_dashboard(result):
    health = result["overall_health"]

    LEVEL_EMOJI = {
        HEALTHY_LEVEL: "🟢",
        NEEDS_ATTENTION_LEVEL: "🟠",
        CRITICAL_LEVEL: "🔴",
    }

    print("\n" + "=" * 55)
    print("BLINDSPOT MAINTENANCE DASHBOARD")
    print("=" * 55)

    # overall health
    emoji = LEVEL_EMOJI[health["level"]]
    print(f"\nOVERALL: {emoji} {health['level'].upper()}")
    print(f"  {health['summary']}")

    # sync module
    print(f"\nSYNC MODULE")
    sync = result["sync_module"]
    sync_emoji = LEVEL_EMOJI[result["overall_health"]["sync_module_level"]]
    print(f"  Status         : {sync_emoji} {sync['status']}")
    print(f"  Local Storage  : {sync['local_storage_status']}")
    print(f"  WiFi           : {sync['wifi_strength']}/5")

    # cameras
    print(f"\nCAMERAS")
    print(f"{'Camera':<12} {'Health':<18} {'Issues'}")
    print("-" * 55)

    for camera in result["cameras"]:
        cam_health = evaluate_camera_health(camera)
        emoji = LEVEL_EMOJI[cam_health["level"]]
        issues = ", ".join(cam_health["issues"]) if cam_health["issues"] else "none"
        print(f"  {camera['name']:<12} {emoji} {cam_health['level']:<16} {issues}")
        for rec in cam_health.get("recommendations", []):
            print(f"  {'':12}   → {rec}")


class MaintenanceDashboard:

    def __init__(self, blink):
        self.blink = blink
        self.camera_manager = CameraManager(blink)
        self.sync_module_manager = SyncModuleManager(blink)

    async def get_dashboard(self):
        camera_statuses = await self.camera_manager.get_all_camera_statuses()
        sync_module_status = await self.sync_module_manager.get_sync_module_status()

        return {
            "overall_health": _evaluate_overall_health(
                camera_statuses, sync_module_status
            ),
            "sync_module": sync_module_status,
            "cameras": camera_statuses,
        }
