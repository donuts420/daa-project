# University Wi-Fi Cost Optimization

A Streamlit dashboard and DAA lab project that connects university buildings
with the minimum total estimated installation cost. It represents buildings as
vertices and possible network links as weighted, undirected edges, then finds a
minimum spanning tree (MST) with a custom heap-based Prim implementation.

> **Cost note:** All costs in the default dataset are illustrative sample
> estimates in Indian rupees. They are not university quotations or verified
> infrastructure prices.

## Problem and objectives

Given a set of campus buildings and candidate connections with estimated costs,
select a set of links that connects every building at the lowest total cost.
The dashboard lets a user edit buildings and links, optimize the network, view
the selected links against all candidates, compare Prim with NetworkX Kruskal,
and validate Prim's result against NetworkX's Kruskal implementation.

## Why an MST?

For a connected, weighted, undirected graph, an MST connects all vertices with
exactly `V - 1` edges and the minimum possible sum of edge weights. This models
the project objective when the only design goal is minimum total installation
cost. The app rejects a disconnected network because it cannot produce a tree
that reaches every building.

An MST does not include extra links for redundancy. Real network planning may
also need to account for backup routes, bandwidth, latency, physical cable
routing, rights of way, equipment, reliability, and operational costs.

## Prim's algorithm

`prim.py` validates the input, trims and checks building names, validates costs
and endpoints, and normalizes duplicate undirected edges by keeping the lowest
cost. It builds an adjacency list and grows a tree from the first building. A
`heapq` min-heap selects the cheapest edge that reaches an unvisited building.
When every building has been reached, the algorithm returns the selected edges
and their total cost. Invalid inputs and disconnected graphs raise a clear
`ValueError`. An empty building list is invalid; a single building has an empty
MST with cost zero.

Pseudocode:

```text
validate buildings and connections
normalize undirected duplicates to their lowest cost
build an adjacency list
mark one building visited
push its outgoing edges into a min-heap

while the heap is not empty and some buildings are unvisited:
    take the lowest-cost edge from the heap
    if it reaches an unvisited building:
        select the edge and mark that building visited
        push its edges to unvisited neighbors

if any building is still unvisited:
    report a disconnected network
return selected edges and their total cost
```

Let `V` be the number of buildings, `M` the number of input connection rows,
and `E` the number of distinct normalized edges. Normalization takes `O(M)`;
building the adjacency list takes `O(V + E)`. Each distinct edge is added to
the heap at most once and heap operations take `O(log V)` for a simple graph,
so total time is `O(M + (V + E) log V)`. The normalized edge map, adjacency
list, heap, and result use `O(V + E)` space. A one-building input returns
immediately with no selected edges.

## Project structure

```text
.
├── app.py                 # Streamlit UI, validation, graph view, and results
├── prim.py                # Independent heap-based Prim implementation
├── requirements.txt       # Runtime dependencies
├── README.md
└── tests/
    ├── test_prim.py       # Input validation and MST behavior
```

## Technology stack

- Python
- Streamlit for the editable dashboard and results
- NetworkX for graph representation, visualization data, and Kruskal validation
- Matplotlib for the static campus graph
- Python `heapq` for Prim's min-heap
- `unittest` for automated tests

Install dependencies from `requirements.txt`:

```text
streamlit
networkx
pandas
matplotlib
```

## Setup and run on Windows

Open PowerShell in the project directory and create a virtual environment:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

In Command Prompt, activate with `.venv\Scripts\activate.bat` instead.
Start the dashboard from the project directory:

```powershell
streamlit run app.py
```

Edit the building and possible connection tables, then select **Optimize
Network**. The graph uses a deterministic layout: gray lines are candidate
connections and red lines are selected MST connections. Candidate edge labels
show installation cost. The comparison reports the sum of normalized candidate
edges, MST cost, estimated savings, and percentage reduction in Indian rupee
format.

## Tests

Run the unit tests from the project directory:

```powershell
python -m unittest discover -s tests -v
```

Optionally compile the project modules:

```powershell
python -m py_compile prim.py app.py tests\test_prim.py
```

## Default sample results

The default buildings are **Administrative Building**, **AB1**, **AB2**,
**AB3**, and **LHC**. The seven candidate connections are:

| Candidate connection | Sample estimated cost |
| --- | ---: |
| Administrative Building – AB1 | ₹1,20,000 |
| Administrative Building – AB2 | ₹1,50,000 |
| AB1 – AB2 | ₹70,000 |
| AB1 – AB3 | ₹1,30,000 |
| AB2 – AB3 | ₹90,000 |
| AB2 – LHC | ₹1,60,000 |
| AB3 – LHC | ₹1,10,000 |

The selected default MST has four connections:

| Selected connection | Sample estimated cost |
| --- | ---: |
| Administrative Building – AB1 | ₹1,20,000 |
| AB1 – AB2 | ₹70,000 |
| AB2 – AB3 | ₹90,000 |
| AB3 – LHC | ₹1,10,000 |

The normalized candidate total is **₹8,30,000**. The optimized network cost is
**₹3,90,000**, estimated savings are **₹4,40,000**, and the cost reduction is
approximately **53.01%**. These figures are based only on the sample values
above and are not actual university quotations.

## Assumptions and limitations

- Every edge is an undirected candidate connection with a finite,
  nonnegative numeric cost.
- Building names must be nonempty and unique after trimming whitespace.
- Self-loops and endpoints that are empty or not in the building list are
  rejected. Repeated undirected links, including reversed rows, use the lowest
  entered cost.
- The network must be connected to produce an MST.
- The model minimizes only the sum of entered edge costs. It does not model
  network capacity, redundancy, latency, physical path constraints, reliability,
  or ongoing maintenance.
- Default costs are illustrative estimates for demonstration and coursework;
  they must be replaced with verified estimates for real planning.

Possible extensions include redundancy-aware network design, additional
engineering constraints, and export of the selected network and cost summary.
