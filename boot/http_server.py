import subprocess, threading
from http.server import BaseHTTPRequestHandler, HTTPServer


html = '''<html><body><table>
<form method="post">
<tr><td>Power</td><td><input type="text" name="power"></td></tr>
<tr><td>Duration</td><td><input type="text" name="duration"></td></tr>
<tr><td><input type="submit" name="submit"></td></tr>
</form></table>
'''

html_end = "</body></html>"


class HTTP_Server(threading.Thread):
    def run(self):
        with HTTPServer(('', 8000), handler) as server:
            server.serve_forever()



class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type','text/html')
        self.end_headers()

        self.wfile.write(bytes(html + html_end, "utf8"))
    def do_POST(self):
        self.send_response(200)
        self.send_header('Content-type','text/html')
        self.end_headers()

        body = self.rfile.read(int(self.headers["Content-Length"])).decode()
        data = body.split("&")

        power = None
        duration = None

        for item in data:
            component = item.split("=")
            key = component[0]
            value = component[1]
            print(key, value)

            if key == "power": power = value
            if key == "duration": duration = value

        p = subprocess.run(["python", "/home/boombrush/Photonic/Remote.py", power, duration])
        #out, err = p.communicate()
        #print(out)

        self.wfile.write(bytes(html + '<img width="100%" src="http://192.168.2.22:8001/imgs/remote.jpg">' + html_end, "utf8"))


server = HTTP_Server()
server.start()

subprocess.run(["python", "-m", "http.server", "8001"])


