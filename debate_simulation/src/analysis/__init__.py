"""Analysis layer: selects and aggregates completed experiment runs.

Reads only from disk. `experiments/` stays append-only — nothing here writes
back into it, so the raw log remains the evidence trail for the paper.
"""
