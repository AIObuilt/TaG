#!/usr/bin/env python3
"""Launch the TaG dashboard."""
import os
import sys
import webbrowser
import threading

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tag.delivery.local.setup_server import serve


def main():
    port = int(os.environ.get("TAG_UI_PORT", "18800"))

    def _open():
        import time
        time.sleep(1)
        webbrowser.open(f"http://localhost:{port}")

    threading.Thread(target=_open, daemon=True).start()
    print(f"TaG dashboard: http://localhost:{port}", flush=True)
    serve(port=port)


if __name__ == "__main__":
    main()
