import asyncio
import unittest
from collections import defaultdict
from threading import Condition, Thread
from typing import Set

from initialize_nodes import do_stuff
from node_manager import Requester, NodeManager


def _run(coroutine):
    return asyncio.get_event_loop().run_until_complete(coroutine)


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


class OfflineTestCase(unittest.TestCase):
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

        _run(nm.complete_neighbourhood(0))

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
            _run(asyncio.wait_for(nm.complete_neighbourhood(0), timeout=5))
        except asyncio.TimeoutError:
            self.fail("Timeout reached!")

        self._assert_graph({i: (set(range(1, 8)) - {i}) for i in range(1, 8)}, req)

    def test_climb_degree(self):
        # intended path:
        # 0 -> 2 (largest) -> 9 (largest) -> 4 (smaller number than 7) -> 3 (smaller number than 4)-> 6 (larger), stop
        req = MockRequester({
            0: {1, 2},
            1: {0},
            2: {0, 1, 9},
            3: {0, 1, 2, 4, 6},
            4: {1, 2, 3, 7, 9},
            6: {1, 2, 3, 4, 5, 7, 8, 9},
            7: {1, 2, 3, 4, 9},
            9: {0, 1, 4, 7}
        })

        nm = NodeManager(req)

        output = _run(nm.climb_degree(0))

        self.assertEqual(6, output)

    def test_distance4(self):
        # intended expansion
        # dist 0: 0
        # dist 1: 1 2 3
        # dist 2: 4 5
        # dist 3: 6 7
        # dist 4: 8 9 10
        req = MockRequester({
            0: {1, 2, 3},
            1: set(),  # path that dies out
            2: {0, 1},  # paths that return
            3: {4, 5, 2},
            4: {5, 6},
            5: {0, 7},
            6: {6, 9},  # path loop
            7: {8, 10}
        })

        nm = NodeManager(req)

        output = _run(nm.distance4(0))

        self.assertEqual({8, 9, 10}, output)


class NetworkTestCases(unittest.TestCase):

    def test(self):
        # OfflineTestCase checks how Requester is used
        # Now just verify that Requester works correctly
        graph = {  # do_stuff creates both connections!
            0: {1, 4, 7},
            1: {0, 4, 5, 6},
            2: {3, 5},
            3: {2, 4},
            4: {0, 1, 3},
            5: {1, 2, 7},
            6: {1, 7},
            7: {0, 5, 6}
        }

        base = 8000
        graph = {k + base: {v + base for v in val} for k, val in graph.items()}

        condition_ready = Condition()
        condition_done = Condition()
        with condition_ready:
            with condition_done:
                thread = Thread(target=do_stuff, daemon=True, args=[
                    "localhost",
                    range(base, base + 8),
                    {(k, v) for k, val in graph.items() for v in val},
                    condition_ready,
                    condition_done])
                thread.start()

                req = Requester("localhost")

                # wait until full initialization
                condition_ready.wait()
                condition_done.notify()

                # check get
                for port in range(base, base + 8):
                    self.assertEqual(graph[port], _run(req.get_connections_from(port)))

                # check add
                _run(req.add_connection(0 + base, 5 + base))
                graph[0 + base].add(5 + base)

                for port in range(base, base + 8):
                    self.assertEqual(graph[port], _run(req.get_connections_from(port)))

                # check bidi add
                _run(req.add_connection_bidi(1 + base, 2 + base))
                graph[1 + base].add(2 + base)
                graph[2 + base].add(1 + base)

                for port in range(base, base + 8):
                    self.assertEqual(graph[port], _run(req.get_connections_from(port)))


if __name__ == '__main__':
    unittest.main()
