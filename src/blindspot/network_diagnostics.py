import socket
import time


def check_port(hostname, port):
    start = time.time()
    try:
        with socket.create_connection((hostname, port), timeout=3) as sock:
            duration_ms = (time.time() - start) * 1000
            return {
                "success": True,
                "host": hostname,
                "port": port,
                "duration_ms": round(duration_ms, 1),
                "error": None,
            }
    except (OSError, TimeoutError, ConnectionRefusedError) as e:
        duration_ms = (time.time() - start) * 1000
        return {
            "success": False,
            "host": hostname,
            "port": port,
            "duration_ms": round(duration_ms, 1),
            "error": str(e),
        }
        pass
