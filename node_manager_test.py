import asyncio
import unittest
from collections import defaultdict
from typing import Set

from node_manager import Requester, NodeManager


# maintains graph as dict of sets, doesn't network
class MockRequester(Requester):
    # noinspection PyMissingConstructor
    def __init__(self, initial_graph: dict, add_sleep: int = 0):
        self._add_sleep = add_sleep
        self._graph = defaultdict(set)
        for key, values in initial_graph.items():
            self._graph[key].update(values)

    def __del__(self):
        pass

    # gets connections from server `from_port`
    async def get_connections_from(self, from_port: int) -> Set[int]:
        return self._graph[from_port]

    # adds `to_port` to connections of `from_port`
    async def add_connection(self, from_port: int, to_port: int) -> None:
        if self._add_sleep > 0:
            await asyncio.sleep(self._add_sleep)
        self._graph[from_port].add(to_port)

    # adds connections both ways
    async def add_connection_bidi(self, port0: int, port1: int) -> None:
        await self.add_connection(port0, port1)
        await self.add_connection(port1, port0)

    def is_connected(self, from_port: int, to_port: int) -> bool:
        return to_port in self._graph[from_port]


class MyTestCase(unittest.TestCase):
    def _assert_graph(self, graph: dict, req: MockRequester):
        for key, values in graph.items():
            for value in values:
                self.assertTrue(req.is_connected(key, value), f'{key} to {value} missing')

    def test_complete_neighbourhood(self):
        req = MockRequester({
            0: {1, 2, 4, 5},
            1: {6},
            2: {5},
            3: {2, 4},
            4: {1},
            5: {1, 7},
            6: {7},
            7: {0, 6}
        })

        nm = NodeManager(req)

        asyncio.get_event_loop().run_until_complete(nm.complete_neighbourhood(0))

        self._assert_graph({
            1: {2, 4, 5},
            2: {1, 4, 5},
            4: {1, 2, 5},
            5: {1, 2, 4}
        }, req)

    def test_concurrent_execution(self):
        req = MockRequester({
            0: {1, 2, 3, 4, 5, 6, 7},
            1: set(),
            2: set(),
            3: set(),
            4: set(),
            5: set(),
            6: set(),
            7: set()
        }, add_sleep=1)

        nm = NodeManager(req)

        try:
            # 7 * 6 / 2 = 21 connections to be added
            asyncio.get_event_loop().run_until_complete(asyncio.wait_for(nm.complete_neighbourhood(0), timeout=5))
        except asyncio.TimeoutError:
            self.fail("Timeout reached!")

        self._assert_graph({i: (set(range(1, 8)) - {i}) for i in range(1, 8)}, req)

    def test_climb_degree(self):
        pass

    def test_distance4(self):
        pass


if __name__ == '__main__':
    unittest.main()
