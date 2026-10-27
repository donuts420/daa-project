"""Prim's minimum spanning tree algorithm for undirected weighted graphs."""

from heapq import heappop, heappush
from math import isfinite
from numbers import Rational, Real


def prim_mst(buildings, connections):
    """Return the minimum spanning tree edges and their total cost.

    ``buildings`` is an iterable of names. ``connections`` is an iterable of
    ``(building_a, building_b, cost)`` records. Names are trimmed before use;
    repeated undirected connections keep only their lowest cost.

    Returns:
        A pair: a list of ``(building_a, building_b, cost)`` MST edges and the
        total cost. Edge endpoints are returned in alphabetical order.

    Raises:
        ValueError: If the input is invalid, empty, or the graph is disconnected.

    Complexity:
        Time: O(M + (V + E) log V), where M is the number of input
        connections, V is the number of buildings, and E is the number of
        distinct connections.
        Space: O(V + E) for the normalized graph, heap, and result.
    """
    if buildings is None or isinstance(buildings, (str, bytes)):
        raise ValueError("Provide at least one building name.")

    try:
        raw_buildings = list(buildings)
    except TypeError as error:
        raise ValueError("Provide at least one building name.") from error

    building_names = []
    for name in raw_buildings:
        if not isinstance(name, str) or not name.strip():
            raise ValueError("Every building name must be a non-empty string.")
        building_names.append(name.strip())

    if not building_names:
        raise ValueError("Provide at least one building name.")
    if len(set(building_names)) != len(building_names):
        raise ValueError("Building names must be unique after trimming whitespace.")

    if connections is None or isinstance(connections, (str, bytes)):
        raise ValueError("Connections must be an iterable of connection records.")
    try:
        connection_iterator = iter(connections)
    except TypeError as error:
        raise ValueError("Connections must be an iterable of connection records.") from error

    known_buildings = set(building_names)
    unique_connections = {}
    for connection in connection_iterator:
        if not isinstance(connection, (tuple, list)) or len(connection) != 3:
            raise ValueError(
                "Each connection must contain two building names and one cost."
            )

        left, right, cost = connection
        if (
            not isinstance(left, str)
            or not isinstance(right, str)
            or not left.strip()
            or not right.strip()
        ):
            raise ValueError("Connection endpoints must be non-empty building names.")
        left, right = left.strip(), right.strip()

        if left not in known_buildings or right not in known_buildings:
            unknown = left if left not in known_buildings else right
            raise ValueError(f"Connection references unknown building: {unknown!r}.")
        if left == right:
            raise ValueError(f"Connection for {left!r} is a self-loop; choose two buildings.")
        if isinstance(cost, bool) or not isinstance(cost, Real):
            raise ValueError("Connection cost must be a finite, nonnegative number.")
        try:
            # Rational values (including arbitrarily large integers) are finite.
            finite_cost = isinstance(cost, Rational) or isfinite(cost)
            valid_cost = finite_cost and cost >= 0
        except (OverflowError, TypeError, ValueError):
            valid_cost = False
        if not valid_cost:
            raise ValueError("Connection cost must be a finite, nonnegative number.")

        # Sorting the endpoints gives each undirected connection one shared key.
        edge = tuple(sorted((left, right)))
        if edge not in unique_connections or cost < unique_connections[edge]:
            unique_connections[edge] = cost

    # Each building maps to its neighboring buildings and the cost to reach them.
    adjacency = {name: [] for name in building_names}
    for (left, right), cost in unique_connections.items():
        adjacency[left].append((cost, right))
        adjacency[right].append((cost, left))

    # The empty graph is invalid; a one-building graph has a valid zero-cost MST.
    visited = {building_names[0]}
    min_heap = []
    for cost, neighbor in adjacency[building_names[0]]:
        heappush(min_heap, (cost, building_names[0], neighbor))

    mst_edges = []
    total_cost = 0
    while min_heap and len(visited) < len(building_names):
        cost, parent, building = heappop(min_heap)
        if building in visited:
            continue

        visited.add(building)
        mst_edges.append((min(parent, building), max(parent, building), cost))
        total_cost += cost

        # Add only edges that can grow the tree to a not-yet-visited building.
        for next_cost, neighbor in adjacency[building]:
            if neighbor not in visited:
                heappush(min_heap, (next_cost, building, neighbor))

    if len(visited) != len(building_names):
        raise ValueError(
            "The network is disconnected; add connections so every building is reachable."
        )

    return mst_edges, total_cost
