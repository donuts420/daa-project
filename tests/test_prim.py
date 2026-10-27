import math
import unittest

from prim import prim_mst


class PrimMSTTests(unittest.TestCase):
    def test_known_graph_returns_minimum_spanning_tree(self):
        buildings = ["Library", "Admin", "Engineering", "Science"]
        connections = [
            ("Library", "Admin", 4),
            ("Library", "Engineering", 2),
            ("Admin", "Engineering", 1),
            ("Admin", "Science", 5),
            ("Engineering", "Science", 8),
            ("Engineering", "Admin", 3),
        ]

        edges, total = prim_mst(buildings, connections)

        self.assertEqual(len(edges), len(buildings) - 1)
        self.assertEqual(total, 8)
        self.assertEqual(
            {(min(left, right), max(left, right), cost) for left, right, cost in edges},
            {("Admin", "Engineering", 1), ("Engineering", "Library", 2),
             ("Admin", "Science", 5)},
        )

    def test_single_building_has_no_edges_and_zero_cost(self):
        self.assertEqual(prim_mst(["Library"], []), ([], 0))

    def test_duplicate_connections_keep_lowest_cost(self):
        edges, total = prim_mst(
            ["Library", "Admin"],
            [("Library", "Admin", 9), ("Library", "Admin", 4)],
        )

        self.assertEqual(edges, [("Admin", "Library", 4)])
        self.assertEqual(total, 4)

    def test_reversed_duplicate_connections_keep_lowest_cost(self):
        edges, total = prim_mst(
            ["Library", "Admin"],
            [("Library", "Admin", 9), ("Admin", "Library", 3)],
        )

        self.assertEqual(edges, [("Admin", "Library", 3)])
        self.assertEqual(total, 3)

    def test_invalid_costs_are_rejected(self):
        for cost in (-1, math.inf, -math.inf, math.nan, "10", True):
            with self.subTest(cost=cost):
                with self.assertRaisesRegex(ValueError, "finite, nonnegative number"):
                    prim_mst(["Library", "Admin"], [("Library", "Admin", cost)])

    def test_large_finite_integer_cost_is_accepted(self):
        cost = 10**400
        self.assertEqual(
            prim_mst(["Library", "Admin"], [("Library", "Admin", cost)]),
            ([("Admin", "Library", cost)], cost),
        )

    def test_unknown_endpoint_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "unknown building"):
            prim_mst(["Library"], [("Library", "Admin", 10)])

    def test_missing_connection_endpoint_is_rejected(self):
        for connection in (
            ("Library", "", 10),
            ("Library", None, 10),
            ("Library", 10),
        ):
            with self.subTest(connection=connection):
                with self.assertRaisesRegex(ValueError, "(?i)connection|endpoints"):
                    prim_mst(["Library", "Admin"], [connection])

    def test_self_loop_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "self-loop"):
            prim_mst(["Library"], [("Library", "Library", 10)])

    def test_disconnected_graph_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "disconnected"):
            prim_mst(["Library", "Admin", "Engineering"], [("Library", "Admin", 10)])

    def test_empty_building_list_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "at least one building"):
            prim_mst([], [])

    def test_invalid_building_names_are_rejected(self):
        for buildings in (["Library", "  "], ["Library", " Library "], ["Library", None]):
            with self.subTest(buildings=buildings):
                with self.assertRaisesRegex(ValueError, "(?i)building name"):
                    prim_mst(buildings, [])


if __name__ == "__main__":
    unittest.main()
