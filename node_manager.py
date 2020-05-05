import asyncio
import itertools

import aiohttp
from typing import Set, Tuple


async def _create_persistent_session():
    return aiohttp.ClientSession()


def _get_persistent_session():
    return asyncio.get_event_loop().run_until_complete(_create_persistent_session())


class Requester:
    def __init__(self, host: str):
        self._host = host
        self._session = _get_persistent_session()

    def __del__(self):
        async with self._session:
            pass

    @staticmethod
    async def _fetch(session, url: str) -> str:
        async with session.get(url) as response:
            return await response.text()

    # gets connections from server `from_port`
    async def get_connections_from(self, from_port: int) -> Set[int]:
        r = await self._fetch(self._session, f'http://{self._host}:{from_port}/')
        return set(map(int, r.split(",")))

    # adds `to_port` to connections of `from_port`
    async def add_connection(self, from_port: int, to_port: int) -> None:
        await self._fetch(self._session, f'http://{self._host}:{from_port}/new?port={to_port}')

    # adds connections both ways
    async def add_connection_bidi(self, port0: int, port1: int) -> None:
        await self.add_connection(port0, port1)
        await self.add_connection(port1, port0)


class NodeManager:
    def __init__(self, requester: Requester):
        self._requester = requester

    async def _add_bidi(self, ports: Tuple[int, int]):
        await self._requester.add_connection_bidi(ports[0], ports[1])

    async def complete_neighbourhood(self, start: int):
        nodes = await self._requester.get_connections_from(start)
        await asyncio.gather(*map(self._add_bidi, itertools.combinations(nodes, 2)))

    async def climb_degree(self, start: int) -> int:
        # maps port to connections, if known, to avoid repeatedly requesting the same information
        degrees = dict()
        degrees[start] = await self._requester.get_connections_from(start)

        while True:
            # find max neighbor
            max_port = start
            print(str(degrees[start]))
            for port in degrees[start]:
                if port not in degrees:
                    degrees[port] = await self._requester.get_connections_from(port)
                if len(degrees[port]) >= len(degrees[max_port]):
                    if len(degrees[port]) == len(degrees[max_port]):
                        max_port = min(port, max_port)
                    else:
                        max_port = port

            # go there if we're not there
            if max_port == start:
                break
            start = max_port

        return max_port

    # gets all that are exactly 1 from this and not present in prev
    async def _next_dist(self, prev: Set[int], this: Set[int]) -> Set[int]:
        unwanted = prev | this
        tmp = await asyncio.gather(*map(self._requester.get_connections_from, this))
        return set(filter(lambda x: x not in unwanted, itertools.chain(*tmp)))

    async def distance4(self, start: int):
        prev = set()
        this = {start}
        for i in range(4):
            next_ = await self._next_dist(prev, this)
            prev |= this
            this = next_
        return this
