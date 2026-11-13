"""Development and WSGI entry point for the portfolio API."""

import os

if __package__:
    from . import create_app
else:
    # Support `python3 app.py` from the backend directory as well as package imports.
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from backend import create_app


app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "5000")))
