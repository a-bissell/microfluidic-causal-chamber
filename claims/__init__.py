"""claims/ — the chamber's claims layer, wired to the lakatos engine.

Phase 1 of the port (see the Lakatos repo's FRAMEWORK.md §7 admissibility
test): a Tier-1 DECIDER over the frozen, committed result CSVs — exhaustive,
deterministic re-checks of the claims the results/*/README.md files make in
prose — plus a battery of those claims expressed as ready-made conjectures
(the engine's zero-plug conjecture_spec path: no oracle, no former needed).

Honesty scope, stated up front: over the FROZEN grids these checks are
total and exhaustive, so within a claim's declared envelope (the committed
sweep cells) the guarantee is real. Beyond the frozen data the refuter
cannot reach — attacking new configurations means new OpenFOAM solves
(Tier 2, phase 4). ROBUST_CONJECTURE here therefore means: unrefuted over
every committed case, envelope = the frozen grid, nothing more.

Run the battery from the repo root:

    python3 -m claims.battery

The lakatos engine is the pip-installable package from the Lakatos repo
(github.com/a-bissell/Lakatos). Install it (`pip install -e ../card_stuff`)
or keep that repo checked out as a sibling directory — imported here with
a path fallback so the battery runs either way.
"""
import sys
from pathlib import Path

try:
    import lakatos  # noqa: F401  (installed: pip install -e ../card_stuff)
except ImportError:                                    # sibling-checkout fallback
    _sibling = Path(__file__).resolve().parents[2] / 'card_stuff'
    if not (_sibling / 'lakatos' / '__init__.py').exists():
        raise ImportError(
            'lakatos engine not found: pip install -e <Lakatos repo> or '
            f'keep it checked out at {_sibling}')
    sys.path.insert(0, str(_sibling))
    import lakatos  # noqa: F401

REPO = Path(__file__).resolve().parents[1]
RESULTS = REPO / 'simulation' / 'openfoam' / 'results'
