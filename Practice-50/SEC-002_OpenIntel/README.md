# SEC-002 OpenIntel

## Version

v1.0

## Description

SEC-002 OpenIntel is an entity processing and search tool.

The tool reads raw input data, normalizes and cleans entities, classifies them, generates statistics, and provides interactive search capability.

## Features

- Read input data from file
- Normalize entities
- Remove empty lines
- Remove duplicate entities
- Entity classification:
  - Emails
  - Domains
  - Names
- Statistics report
- Interactive search engine

## Project Structure

```text
SEC-002_OpenIntel
│
├── data
│   └── input.txt
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

1. Read raw entities
2. Normalize data
3. Remove duplicate values
4. Classify entities
5. Generate report
6. Search entities interactively

## Example

### Input

```text
john@example.com
google.com
John Smith
```

### Output

```text
Emails:

john@example.com

Domains:

google.com

Names:

john smith
```

## Future Roadmap

Future versions may include:

- Advanced validation
- Entity relationships
- Relationship analysis
- Graph-based intelligence