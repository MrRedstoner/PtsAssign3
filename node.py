from urllib.parse  import urlparse, parse_qs
from http.server  import BaseHTTPRequestHandler


def get_handler():
    neighbours = set()
    class MyHandler(BaseHTTPRequestHandler):
        def _set_headers(self):
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()

        def do_GET(self):
            nonlocal neighbours
            self._set_headers()
            response = 'http://localhost:8000/ or http://localhost:8000/new?port=8080'

            parsed = urlparse(self.path)
            pquery = parse_qs(parsed.query)
            self._root = '..'
            if parsed.path == '/':
                response = ','.join(neighbours)
            if parsed.path == '/new':
                self._name = pquery.get('port', (None,))[0]
                if self._name is not None:
                    neighbours.add(self._name)
                    response = 'Added or exists.'
                else:
                    response = 'Nothing to add.'

            self.wfile.write(bytes(response, "UTF-8"))
    
        def do_HEAD(self):
            self._set_headers()

    return MyHandler






