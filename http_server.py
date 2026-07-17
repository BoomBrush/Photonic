import http.server
import socketserver

PORT = 8000

Handler = http.server.SimpleHTTPRequestHandler

try:
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print("serving at port", PORT)
        httpd.serve_forever()
except OSError:
    print("HTTP Server already running")
