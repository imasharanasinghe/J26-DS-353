"""Start the C4 web workbench.

    python3 scripts/run_c4_server.py            # http://127.0.0.1:8765
    python3 scripts/run_c4_server.py --port 9000 --open
"""

from __future__ import annotations

import argparse
import sys
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from c4.server import create_server, ollama_status


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1", help="Keep the default: the server has no authentication")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--open", action="store_true", help="Open the workbench in the default browser")
    args = parser.parse_args()

    server = create_server(args.host, args.port)
    url = f"http://{args.host}:{args.port}/"
    status = ollama_status()
    print(f"C4 workbench running at {url}  (Ctrl+C to stop)")
    print("Ollama:", "online" if status["online"] else "offline (drafting needs it; verifying pasted text still works)")
    if args.open:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
