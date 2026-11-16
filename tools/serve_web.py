"""Serve this checkout as the web version of the game, for a look in a browser.

The page lives in web/, but every asset it loads lives in the folders beside it -
chars/, stages/, data/, font/, sound/. So the server's root is the checkout, not
web/: /web/index.html is the game and /chars/kfm/kfm.sff is the sprite it draws.
One folder, one copy of the art, both versions reading it.

Range requests are answered properly because mugen-js reads sprites in ranges; a
server that ignores Range still works, it just sends whole files.

Run:  python3 tools/serve_web.py            # http://127.0.0.1:8123/web/
      python3 tools/serve_web.py --port 9000 --host 0.0.0.0
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Handler(SimpleHTTPRequestHandler):
    """Static files with Range support and no caching, so an edit is a reload."""

    def translate_path(self, path):
        """The game is at /, while the assets stay at /chars, /data and so on.

        The page lives in web/ but the folders it reads are beside it, so the
        server's root cannot be web/. Serving web/index.html for the root keeps
        both halves on one origin - and stops the root from being a directory
        listing of the whole checkout.
        """
        clean = path.split("?", 1)[0].split("#", 1)[0].rstrip("/")
        if clean in ("", "/index.html", "/web", "/web/index.html"):
            return os.path.join(self.directory, "web", "index.html")
        return super().translate_path(path)

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def send_head(self):
        header = self.headers.get("Range")
        path = self.translate_path(self.path)
        if not header or not os.path.isfile(path):
            return super().send_head()
        size = os.path.getsize(path)
        m = re.match(r"bytes=(\d*)-(\d*)$", header.strip())
        if not m:
            return super().send_head()
        start = int(m.group(1)) if m.group(1) else 0
        end = int(m.group(2)) if m.group(2) else size - 1
        end = min(end, size - 1)
        if start >= size or start > end:
            self.send_error(416, "Range Not Satisfiable")
            return None
        handle = open(path, "rb")
        handle.seek(start)
        self.send_response(206)
        self.send_header("Content-Type", self.guess_type(path))
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
        self.send_header("Content-Length", str(end - start + 1))
        self.end_headers()
        return _Slice(handle, end - start + 1)


class _Slice:
    """A file handle that stops after n bytes, which copyfile() honours."""

    def __init__(self, handle, length):
        self.handle = handle
        self.left = length

    def read(self, amount=-1):
        amount = self.left if amount < 0 else min(amount, self.left)
        data = self.handle.read(amount)
        self.left -= len(data)
        return data

    def close(self):
        self.handle.close()


def main():
    ap = argparse.ArgumentParser(description="Serve the web build from this checkout")
    ap.add_argument("--port", type=int, default=8123)
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--root", default=ROOT)
    args = ap.parse_args()

    handler = partial(Handler, directory=args.root)
    server = ThreadingHTTPServer((args.host, args.port), handler)
    print(f"serving {args.root} at http://{args.host}:{args.port}/web/", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print()
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
