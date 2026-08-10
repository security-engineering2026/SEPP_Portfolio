# SEC-004 DataFusion

## Version

v1.0

## Description

SEC-004 DataFusion imports graph data produced by previous tools and converts it into a structured dataset for analysis.

The tool reads graph relations, extracts nodes, calculates node frequency, identifies the most frequent node, and generates a unified fusion report.

## Features

- Read graph file
- Normalize input
- Build structured relations
- Extract unique nodes
- Calculate node frequency
- Find most frequent node
- Generate fusion summary report

## Project Structure

```text
SEC-004_DataFusion
│
├── data
│   └── graph.txt
│
├── output
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

1. Read graph data
2. Normalize lines
3. Split source and target
4. Build structured relations
5. Extract unique nodes
6. Calculate node frequency
7. Find the most frequent node
8. Generate final report

## Example

### Input

```text
john@example.com -> example.com
```

### Output

```text
Imported Relations : 1
Total Nodes        : 2

Nodes
-----
- john@example.com
- example.com
```

## Future Roadmap

Future versions may include:

- Multi-file fusion
- Asset + Graph fusion
- Entity enrichment
- Frequency ranking
- JSON export
- Risk scoring