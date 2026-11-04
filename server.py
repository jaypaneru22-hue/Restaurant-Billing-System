"""RestoPro Multi-User HTTP Server & REST API Entrypoint.

Starts the multi-threaded HTTP server allowing simultaneous customer access from mobile phones,
laptops, tablets, and desktop browsers over localhost, local area network (LAN), or public internet.
"""
import os
import sys
import argparse
from pathlib import Path

# Ensure root directory is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from database.db import db
from database.migrations import initialize_database
from api.http_server import run_http_server
from utils.logger import logger


def get_local_ip() -> str:
    """Discovers machine's local Wi-Fi / LAN IP address for multi-device access."""
    import socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Connect to an external IP (does not actually send packets)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def main():
    parser = argparse.ArgumentParser(description="RestoPro Multi-User HTTP Backend Server")
    parser.add_argument("--host", default=os.getenv("RESTOPRO_HOST", "0.0.0.0"), help="Host address (default 0.0.0.0 for LAN access)")
    parser.add_argument("--port", type=int, default=int(os.getenv("RESTOPRO_PORT", 8080)), help="Port number (default 8080)")
    args = parser.parse_args()

    # Ensure database is initialized with all tables & constraints
    initialize_database(db)

    local_ip = get_local_ip()
    port = args.port
    host = args.host

    banner = f"""
======================================================================
  🍽️ RESTOPRO — RESTAURANT MANAGEMENT PLATFORM (MULTI-USER ENGINE)
======================================================================
  • Listening on Host       : {host}
  • Port                    : {port}
  • Local Machine Access    : http://127.0.0.1:{port}/
  • Multi-Device LAN Access : http://{local_ip}:{port}/
  • Customer Mobile Portal  : http://{local_ip}:{port}/portal
  • REST API Endpoint       : http://{local_ip}:{port}/api
======================================================================
  Multiple customers can simultaneously connect, register, place orders,
  and track tickets from phones, tablets, and laptops.
======================================================================
"""
    print(banner)
    logger.info(f"Starting RestoPro HTTP server on {host}:{port}")

    httpd = run_http_server(host=host, port=port)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down RestoPro HTTP Server...")
        httpd.shutdown()
        logger.info("RestoPro HTTP Server stopped cleanly.")


if __name__ == "__main__":
    main()
