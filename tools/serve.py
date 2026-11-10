# SPDX-FileCopyrightText: 2026 Jessica Breen
# SPDX-License-Identifier: GPL-3.0-or-later
"""
Local web server for working on Diamond Painting with Data.

Run from the repository root:
    python3 tools/serve.py            (then open http://localhost:8000)
    python3 tools/serve.py 8080       (use a different port)

It serves the site like `python3 -m http.server`, with two extras:
  * Whenever the game asks for the level list, it first checks whether any
    painting in art/ or any level file in tools/ has changed since the last
    build, and if so rebuilds the levels. Save in the editor, reload the
    game, and the change is there.
  * It tells the browser not to keep old copies of the level files.
"""

import http.server
import os
import subprocess
import sys

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
CATALOGUE = os.path.join(ROOT, "levels", "levels.json")


def newest_source():
    newest = 0
    for folder in ("art", "tools"):
        for dirpath, _, files in os.walk(os.path.join(ROOT, folder)):
            if "__pycache__" in dirpath:
                continue
            for f in files:
                if f.endswith((".grid.json", ".py")):
                    newest = max(newest, os.path.getmtime(os.path.join(dirpath, f)))
    return newest


def rebuild_if_needed():
    built = os.path.getmtime(CATALOGUE) if os.path.exists(CATALOGUE) else 0
    if newest_source() > built:
        print("Paintings or level files changed: rebuilding levels…", flush=True)
        result = subprocess.run([sys.executable, os.path.join(ROOT, "tools", "build_levels.py")],
                                cwd=ROOT, capture_output=True, text=True)
        print(result.stdout + result.stderr, flush=True)
        if result.returncode != 0:
            print("The build failed; the game is still showing the last good build.", flush=True)


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=ROOT, **kwargs)

    def do_GET(self):
        if self.path.split("?")[0].endswith("levels/levels.json"):
            rebuild_if_needed()
        super().do_GET()

    def end_headers(self):
        self.send_header("Cache-Control", "no-cache")
        super().end_headers()


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    rebuild_if_needed()
    print(f"Serving {ROOT}\n  Game:   http://localhost:{port}/\n  Editor: http://localhost:{port}/tools/editor.html\n"
          "Press Ctrl+C to stop.", flush=True)
    with http.server.ThreadingHTTPServer(("", port), Handler) as server:
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\nStopped.")


if __name__ == "__main__":
    main()
