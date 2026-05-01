"""Production-ish entrypoint for Windows using Waitress.

Run with: python serve.py
Reads HOST/PORT from env (defaults: 0.0.0.0:5000).
"""

import os

from waitress import serve

from app import create_app


def main() -> None:
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "5000"))
    app = create_app()
    print(f"NeuroFlow rodando em http://{host}:{port} (Ctrl+C para parar)")
    serve(app, host=host, port=port, threads=8)


if __name__ == "__main__":
    main()
