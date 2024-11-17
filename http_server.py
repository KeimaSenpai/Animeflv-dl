import sys
from http.server import BaseHTTPRequestHandler, HTTPServer

try:
    port = int(sys.argv[1])
except IndexError:
    port = 80


class MyServer(BaseHTTPRequestHandler):

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(bytes("200 OK - It's working!", "utf-8"))


webServer = HTTPServer(("0.0.0.0", port), MyServer)
print(f"[!] Server running on port {port}...")
webServer.serve_forever()
