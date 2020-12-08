from http.server import BaseHTTPRequestHandler, HTTPServer


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b'VERIFIED')


def main():
    httpd = HTTPServer(('127.0.0.1', 5005), Handler)
    httpd.serve_forever()


if __name__ == "__main__":
    main()
