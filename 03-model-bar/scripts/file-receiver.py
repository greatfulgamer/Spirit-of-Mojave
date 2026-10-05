import http.server, os

DST = os.path.expanduser("~/Documents/portraits-incoming")
os.makedirs(DST, exist_ok=True)

class H(http.server.BaseHTTPRequestHandler):
    def do_PUT(self):
        name = os.path.basename(self.path)
        if not name:
            self.send_error(400)
            return
        path = os.path.join(DST, name)
        n = int(self.headers.get("Content-Length", 0))
        with open(path, "wb") as f:
            left = n
            while left > 0:
                c = self.rfile.read(min(65536, left))
                if not c:
                    break
                f.write(c)
                left -= len(c)
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK\n")

    def do_GET(self):
        if self.path == "/ping":
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"pong\n")
        else:
            self.send_error(404)

    def log_message(self, *a):
        pass

http.server.HTTPServer(("0.0.0.0", 8899), H).serve_forever()
