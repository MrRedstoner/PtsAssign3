from typing import Set


class Requester:
    # gets connections from server `from_port`
    def get_connections_from(self, from_port: int) -> Set[int]:
        pass

    # adds `to_port` to connections of `from_port`
    def add_connection(self, from_port: int, to_port: int) -> bool:
        pass

    # adds connections both ways
    def add_connection_bidi(self, port0: int, port1: int) -> bool:
        return self.add_connection(port0, port1) and self.add_connection(port1, port0)


class NodeManager:
    def __init__(self, requester: Requester):
        self._requester = requester

    async def complete_neighbourhood(self, start: int):
        pass

    async def climb_degree(self, start: int):
        pass

    async def distance4(self, start: int):
        pass
