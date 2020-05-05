import asyncio
import aiohttp
from typing import Set


async def _create_persistent_session():
    return aiohttp.ClientSession()


def _get_persistent_session():
    return asyncio.get_event_loop().run_until_complete(_create_persistent_session())


class Requester:
    def __init__(self, host: str):
        self._host = host
        self._session = _get_persistent_session()

    def __del__(self):
        with self._session:
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

    async def _add_bidi(self, v0: int, v1: int):
        await self._requester.add_connection_bidi(v0, v1)

    async def complete_neighbourhood(self, start: int):
        nodes = list(await self._requester.get_connections_from(start))
        tasks = list()
        for x in range(len(nodes)):
            for y in range(x + 1, len(nodes)):
                tasks.append(self._add_bidi(nodes[x], nodes[y]))
        await asyncio.gather(*tasks)

    async def climb_degree(self, start: int):
        pass

    async def distance4(self, start: int):
        pass
