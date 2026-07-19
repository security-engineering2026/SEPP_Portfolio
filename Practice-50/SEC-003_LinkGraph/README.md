# SEC-003 LinkGraph

## Version

v1.0

## Description

SEC-003 LinkGraph builds a simple relationship graph from discovered entities.

The tool extracts relationships between emails and domains, builds graph nodes, calculates node degree, finds the most connected node, exports the graph, imports it back, and supports graph search.

## Features

- Read entities
- Normalize data
- Remove empty lines
- Remove duplicate entities
- Entity classification
- Build relationships
- Extract graph nodes
- Calculate node degree
- Find most connected node
- Export graph
- Import graph
- Graph search

## Project Structure

```
SEC-003_LinkGraph
│
├── data
│   └── entities.txt
│
├── output
│   ├── graph.txt
│   └── .gitkeep
│
├── src
│   └── main.py
│
├── README.md
├── CHANGELOG.md
└── requirements.txt
```

## How It Works

1. Read entities
2. Normalize input
3. Remove duplicates
4. Classify entities
5. Build relationships
6. Extract graph nodes
7. Calculate node degree
8. Find the most connected node
9. Export graph
10. Import graph
11. Search graph

## Future Roadmap

Future versions may include:

- Domain-to-domain relationships
- Name-to-email relationships
- Graph visualization
- JSON export
- Graph statistics