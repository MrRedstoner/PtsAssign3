from typing import Set

import requests


class Requester:
    def __init__(self, host: str):
        self._host = host

    # gets connections from server `from_port`
    def get_connections_from(self, from_port: int) -> Set[int]:
        r = requests.get(f'http://{self._host}:{from_port}/')
        return set(map(int, r.content.decode("UTF-8").split(",")))

    # adds `to_port` to connections of `from_port`
    def add_connection(self, from_port: int, to_port: int) -> None:
        _ = requests.get(f'http://{self._host}:{from_port}/new?port={to_port}')

    # adds connections both ways
    def add_connection_bidi(self, port0: int, port1: int) -> None:
        self.add_connection(port0, port1)
        self.add_connection(port1, port0)


class NodeManager:
    def __init__(self, requester: Requester):
        self._requester = requester

    def complete_neighbourhood(self, start: int):
        nodes = self._requester.get_connections_from(start)
        for x in nodes:
            for y in nodes:
                if x != y:
                    self._requester.add_connection_bidi(x, y)

    async def climb_degree(self, start: int):
        pass

    async def distance4(self, start: int):
        pass
