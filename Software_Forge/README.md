# Software Forge — Master Product Manifest v1.2

This directory contains the current Product Contract for Software Forge.

Files:
- SOFTWARE_FORGE_MASTER_MANIFEST_v1.2.yaml — current machine-oriented Product Contract.

Version history:
- v1.0 — baseline Product Contract.
- v1.1 — Product Intelligence / Similar Product Analysis foundation.
- v1.2 — large-scale Product Intelligence Search Engine contract plus offline-first engineering, local intelligence, pre-provisioning, dependency/toolchain/documentation caches, knowledge packs, integrity verification and online/offline transition requirements.

Critical rules:
- The Manifest is the Product Contract, not the implementation.
- Product Intelligence is a search-and-analysis system, not a fixed three-product comparison.
- Discovery must support large candidate pools, multi-source retrieval, deduplication, relevance filtering and adaptive search depth.
- External observations never silently become requirements.
- Product Intelligence must preserve provenance and distinguish documented fact, observation, inference and recommendation.
- Contract changes require explicit approval and a new Manifest version.
- When online, Forge should proactively provision approved offline capabilities and verify their integrity.
- When offline, Forge must continue all locally provisioned engineering and intelligence capabilities instead of waiting on the network.
- Missing online-only capability must be explicit UNKNOWN/BLOCKED rather than silently treated as PASS.
- Implementation and release claims require real CI/runtime evidence and independent verification.

GitHub branch:
software-forge-manifest-v1.0
