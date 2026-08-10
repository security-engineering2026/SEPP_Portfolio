# SEC-005 AnalysisEngine

## Version

v1.0

## Description

SEC-005 AnalysisEngine consumes frequency data produced by SEC-004 DataFusion and performs risk analysis, prioritization, filtering, and reporting.

## Features

- Read frequency file
- Parse node/count data
- Risk classification
- Numeric risk scoring
- Build structured risk report
- Sort by score
- Filter high-risk findings
- Generate top findings
- Export report to file

## Pipeline

SEC-004 -> frequency.txt -> SEC-005 -> report.txt