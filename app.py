

import math
import textwrap

import matplotlib.pyplot as plt
import networkx as nx
import pandas as pd
import streamlit as st

from prim import prim_mst


DEFAULT_BUILDINGS = [
    "Administrative Building",
    "AB1",
    "AB2",
    "AB3",
    "LHC",
]

DEFAULT_CONNECTIONS = [
    ("Administrative Building", "AB1", 120_000),
    ("Administrative Building", "AB2", 150_000),
    ("AB1", "AB2", 70_000),
    ("AB1", "AB3", 130_000),
    ("AB2", "AB3", 90_000),
    ("AB2", "LHC", 160_000),
    ("AB3", "LHC", 110_000),
]


def _snapshot(buildings_table, connections_table):
    """Return a stable value for detecting edits and clearing stale results."""
    return (
        buildings_table.to_json(orient="split"),
        connections_table.to_json(orient="split"),
    )


def _make_candidate_graph(buildings, connections):
    """Build the visualization graph, keeping the cheapest duplicate edge."""
    graph = nx.Graph()
    graph.add_nodes_from(name.strip() for name in buildings)

    for left, right, cost in connections:
        left, right = left.strip(), right.strip()
        if graph.has_edge(left, right):
            graph[left][right]["weight"] = min(graph[left][right]["weight"], cost)
        else:
            graph.add_edge(left, right, weight=cost)
    return graph


def _format_rupees(amount):
    negative = amount < 0
    display = f"{abs(amount):.0f}" if amount == int(amount) else f"{abs(amount):.2f}"
    whole, decimal_point, fraction = display.partition(".")
    if len(whole) > 3:
        tail, prefix = whole[-3:], whole[:-3]
        groups = [tail]
        while prefix:
            groups.append(prefix[-2:])
            prefix = prefix[:-2]
        whole = ",".join(reversed(groups))
    sign = "-" if negative else ""
    return f"₹{sign}{whole}{decimal_point}{fraction}"


def _draw_network(graph, selected_edges):
    """Create a compact static view of candidate connections and the MST."""
    positions = nx.spring_layout(graph, seed=24, k=1.1, iterations=100, weight=None)
    figure, axis = plt.subplots(figsize=(8.2, 4.8))
    selected_pairs = {frozenset((left, right)) for left, right, _ in selected_edges}
    selected_edges_graph = [
        (left, right)
        for left, right in graph.edges
        if frozenset((left, right)) in selected_pairs
    ]

    nx.draw_networkx_edges(
        graph, positions, ax=axis, edge_color="#a8b0bd", width=1.8, alpha=0.9
    )
    nx.draw_networkx_edges(
        graph, positions, edgelist=selected_edges_graph, ax=axis,
        edge_color="#dc2626", width=3.2,
    )
    nx.draw_networkx_nodes(
        graph, positions, ax=axis, node_color="#dbeafe", edgecolors="#2563eb",
        linewidths=1.5, node_size=900,
    )

    # Put wrapped building names just outside the nodes to avoid clipping the long default name.
    labels = {name: textwrap.fill(name, width=15) for name in graph.nodes}
    label_positions = {name: point * 1.18 for name, point in positions.items()}
    nx.draw_networkx_labels(
        graph, label_positions, labels=labels, ax=axis, font_size=8,
        font_weight="normal", bbox={"boxstyle": "round,pad=0.25", "fc": "white", "ec": "#cbd5e1", "alpha": 0.95},
    )
    edge_labels = {
        (left, right): _format_rupees(data["weight"])
        for left, right, data in graph.edges(data=True)
    }
    nx.draw_networkx_edge_labels(
        graph, positions, edge_labels=edge_labels, ax=axis, font_size=8,
        rotate=False, label_pos=0.5,
        bbox={"boxstyle": "round,pad=0.12", "fc": "white", "ec": "none", "alpha": 0.9},
    )

    axis.set_xlim(-1.65, 1.65)
    axis.set_ylim(-1.45, 1.45)
    axis.set_axis_off()
    figure.tight_layout(pad=0.5)
    return figure


st.set_page_config(page_title="University Wi-Fi Cost Optimization", layout="wide")
st.title("University Wi-Fi Cost Optimization")
st.write(
    "Connect every campus building at minimum estimated installation cost using "
    "Prim's Minimum Spanning Tree algorithm."
)
st.caption("The default sample network has 5 buildings; its MST uses 4 connections at an estimated ₹390,000.")

# Keep editor data and the last valid result across Streamlit reruns.
if "buildings" not in st.session_state:
    st.session_state.buildings = DEFAULT_BUILDINGS.copy()
if "connections" not in st.session_state:
    st.session_state.connections = [list(row) for row in DEFAULT_CONNECTIONS]
if "optimization_result" not in st.session_state:
    st.session_state.optimization_result = None
if "optimization_error" not in st.session_state:
    st.session_state.optimization_error = None
st.subheader("Campus network data")
left_column, right_column = st.columns([1, 2])

with left_column:
    st.markdown("**Buildings**")
    buildings_table = st.data_editor(
        pd.DataFrame({"Building": st.session_state.buildings}),
        num_rows="dynamic",
        hide_index=True,
        width="stretch",
        key="building_editor",
        column_config={"Building": st.column_config.TextColumn("Building name")},
    )

with right_column:
    st.markdown("**Possible network connections**")
    connections_table = st.data_editor(
        pd.DataFrame(
            st.session_state.connections,
            columns=["Building A", "Building B", "Installation Cost (₹, sample estimate)"],
        ),
        num_rows="dynamic",
        hide_index=True,
        width="stretch",
        key="connection_editor",
        column_config={
            "Building A": st.column_config.TextColumn("Building A"),
            "Building B": st.column_config.TextColumn("Building B"),
            "Installation Cost (₹, sample estimate)": st.column_config.NumberColumn(
                "Installation Cost (₹, sample estimate)",
                min_value=0.0,
                step=1000.0,
                format="localized",
            ),
        },
    )

# Store the edited tables so changes remain available after each rerun.
st.session_state.buildings = buildings_table["Building"].tolist()
st.session_state.connections = connections_table.values.tolist()
current_snapshot = _snapshot(buildings_table, connections_table)
if current_snapshot != st.session_state.get("input_snapshot"):
    st.session_state.input_snapshot = current_snapshot
    st.session_state.optimization_result = None
    st.session_state.optimization_error = None

if st.button("Optimize Network", type="primary"):
    try:
        building_names = buildings_table["Building"].tolist()
        connections = connections_table.itertuples(index=False, name=None)
        selected_edges, prim_cost = prim_mst(building_names, connections)

        candidate_graph = _make_candidate_graph(
            building_names,
            connections_table.itertuples(index=False, name=None),
        )
        kruskal_tree = nx.minimum_spanning_tree(
            candidate_graph,
            algorithm="kruskal",
            weight="weight",
        )
        kruskal_cost = sum(data["weight"] for _, _, data in kruskal_tree.edges(data=True))
        costs_match = prim_cost == kruskal_cost or math.isclose(
            prim_cost,
            kruskal_cost,
            rel_tol=1e-9,
            abs_tol=1e-9,
        )

        st.session_state.optimization_result = {
            "edges": selected_edges,
            "total_cost": prim_cost,
            "kruskal_cost": kruskal_cost,
            "costs_match": costs_match,
            "graph": candidate_graph,
        }
        st.session_state.optimization_error = None
    except (ValueError, TypeError, OverflowError) as error:
        st.session_state.optimization_result = None
        st.session_state.optimization_error = str(error)

if st.session_state.optimization_error:
    st.error(st.session_state.optimization_error)

result = st.session_state.optimization_result
if result:
    edges = result["edges"]
    total_cost = result["total_cost"]
    st.subheader("Optimized network")
    metric_columns = st.columns(3)
    metric_columns[0].metric("Buildings", len(buildings_table))
    metric_columns[1].metric("Selected connections", len(edges))
    metric_columns[2].metric("Minimum total cost", _format_rupees(total_cost))

    candidate_cost = sum(data["weight"] for _, _, data in result["graph"].edges(data=True))
    estimated_savings = candidate_cost - total_cost
    cost_reduction = estimated_savings / candidate_cost * 100 if candidate_cost else 0
    st.markdown("**Cost comparison**")
    comparison_columns = st.columns(4)
    comparison_columns[0].metric("Cost of all candidate connections", _format_rupees(candidate_cost))
    comparison_columns[1].metric("Optimized network cost", _format_rupees(total_cost))
    comparison_columns[2].metric("Estimated savings", _format_rupees(estimated_savings))
    comparison_columns[3].metric("Cost reduction (%)", f"{cost_reduction:.2f}%")
    st.caption("Savings are estimates based on illustrative sample installation costs.")

    if len(edges) == len(buildings_table) - 1:
        st.success(f"The MST connects all {len(buildings_table)} buildings with {len(edges)} connections.")
    if result["costs_match"]:
        st.info(f"Kruskal validation agrees: {_format_rupees(result['kruskal_cost'])}.")
    else:
        st.warning(
            "Prim and Kruskal returned different total costs. Check the network data "
            "and algorithm inputs."
        )

    selected_table = pd.DataFrame(
        [
            {
                "Building A": left,
                "Building B": right,
                "Installation Cost (₹)": cost,
            }
            for left, right, cost in edges
        ]
    )
    st.markdown("**Selected MST connections**")
    st.dataframe(selected_table, hide_index=True, width="stretch")

    if len(result["graph"].edges) < len(connections_table):
        st.caption("Duplicate undirected connections were combined; the lowest sample cost was used.")

    st.markdown("**Candidate connections and selected MST**")
    st.caption("Gray lines show candidate connections; red lines show the selected MST.")
    figure = _draw_network(result["graph"], edges)
    try:
        _, graph_column, _ = st.columns([1, 4, 1])
        with graph_column:
            st.pyplot(figure, width="content")
    finally:
        plt.close(figure)
else:
    st.info("Edit the campus data if needed, then select **Optimize Network** to calculate the MST.")
