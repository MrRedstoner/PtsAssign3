from urllib.parse import urlparse, parse_qs
from http.server import BaseHTTPRequestHandler


def get_handler():
    neighbours = set()

    class MyHandler(BaseHTTPRequestHandler):
        def _set_headers(self):
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()

        # noinspection PyPep8Naming
        def do_GET(self):
            nonlocal neighbours
            self._set_headers()
            response = 'http://localhost:8000/ or http://localhost:8000/new?port=8080'

            parsed = urlparse(self.path)
            parsed_query = parse_qs(parsed.query)
            if parsed.path == '/':
                response = ','.join(neighbours)
            if parsed.path == '/new':
                name = parsed_query.get('port', (None,))[0]
                if name is not None:
                    neighbours.add(name)
                    response = 'Added or exists.'
                else:
                    response = 'Nothing to add.'

            self.wfile.write(bytes(response, "UTF-8"))

        # noinspection PyPep8Naming
        def do_HEAD(self):
            self._set_headers()

    return MyHandler
