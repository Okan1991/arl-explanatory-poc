# arl-explanatory-poc
Deterministic proof of concept for interpreting FHIR observations and detecting convergent health patterns (non-diagnostic).

# ARL Explanatory Proof of Concept

This repository contains a small, deterministic proof of concept (PoC) for interpreting health observations (FHIR format) and detecting convergent patterns across multiple independent markers.

The goal is to make the ARL idea concrete and test feasibility, i.e., not to provide clinical decision support.

---

## What this PoC DOES

- Parses a small set of FHIR Observation resources
- Interprets observations using a curated, versioned knowledge pack
- Produces human-readable explanations per marker
- Detects convergence when multiple independent markers point to a shared risk pattern
- Applies explicit guardrails (e.g. unit mismatch rejection)
- Outputs transparent, auditable JSON

---

## What this PoC DOES NOT do

-  No diagnosis
-  No prediction
-  No machine learning
-  No automated clinical decision-making
-  No causal claims

Convergence is treated as a plausibility heuristic, not as proof.

---

## Design principles

- **Deterministic**: rule-based, no black box
- **Curated knowledge**: clinical semantics live in a knowledge pack, not in code
- **Traceable**: every output can be explained
- **Non-diagnostic** by design

---

## Repository structure

arl-explanatory-poc/

---

## How to run the demo

```bash
python cvd_demo_run.py
```
---

## Optional safety test (unit mismatch)

```bash
python cvd_demo_run_unit_mismatch.py
```
---

## Disclaimer

This repository is a technical proof of concept.

Any clinical thresholds, interpretations, or references are illustrative and curated for demonstration purposes only and must not be used for medical decision-making.

---
