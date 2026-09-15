"""claims/refit.py — machine refit of the sweep's slug-length scaling law.

Port phase 3, the fitter side. THIS MODULE MUST NOT KNOW THE ANSWER: it
never names the literature law it is re-deriving, never contains its
published coefficients, and never imports the repo's validation script.
claims/refit_acceptance.py enforces that boundary mechanically by scanning
this file's source (plus the data layer and the engine fitter it builds
on) — the same no-hints discipline the engine's own former acceptance
uses. The comparison to the published law happens only on the checker
side.

Protocol, all in exact rational arithmetic (Fraction), least squares
nowhere:

  1. exact_refusal(): lakatos.fitter.exact_fit over the raw sweep rows.
     Real measurements are noisy, no exact affine law fits them, and the
     fitter must REFUSE rather than hallucinate — refusal is the expected,
     honest outcome, demonstrated rather than assumed.
  2. minimax_affine(): every support pair of rows proposes the exact line
     through it; the line minimizing the maximum absolute residual over
     ALL rows wins. Deterministic, exact per candidate line, and the
     winning residual is reported as the law's empirical tolerance.
  3. minimax_plane(): the same enumeration over support triples with the
     capillary number as a second atom — does a second dimensionless
     group materially tighten the fit, and with what sign?
"""
from fractions import Fraction
from itertools import combinations

from lakatos.fitter import FeatureBasis, exact_fit

from claims.frozen import SWEEP


def sweep_points():
    """(q, Ca, L_over_w) as exact Fractions for the velocity-driven rows
    that completed (the frozen scaling dataset)."""
    return [(Fraction(r['q_ratio']), Fraction(r['Ca']),
             Fraction(r['L_over_w']))
            for r in SWEEP if r['mode'] == 'velocity' and r['status'] == 'ok']


def exact_refusal():
    """True iff the engine's exact fitter refuses the raw rows (returns
    None): no exact affine-in-q law reproduces noisy measurements, and the
    fitter must say so instead of inventing one."""
    pts = sweep_points()
    basis = FeatureBasis(('q',), lambda pt: {'q': pt['q']})
    sol = exact_fit(basis, [{'q': q} for q, _, _ in pts],
                    [y for _, _, y in pts])
    return sol is None


def minimax_affine():
    """Best two-point-support affine law y = a + b*q by minimax residual.
    Returns (a, b, max_residual, n_rows), all exact Fractions."""
    pts = sweep_points()
    best = None
    for (q1, _, y1), (q2, _, y2) in combinations(pts, 2):
        if q1 == q2:
            continue
        b = (y2 - y1) / (q2 - q1)
        a = y1 - b * q1
        res = max(abs(y - (a + b * q)) for q, _, y in pts)
        if best is None or res < best[0]:
            best = (res, a, b)
    res, a, b = best
    return a, b, res, len(pts)


def minimax_plane():
    """Best three-point-support plane y = a + bq*q + bc*Ca by minimax
    residual. Returns (a, bq, bc, max_residual)."""
    pts = sweep_points()
    best = None
    for p1, p2, p3 in combinations(pts, 3):
        (q1, c1, y1), (q2, c2, y2), (q3, c3, y3) = p1, p2, p3
        d = (q2 - q1) * (c3 - c1) - (q3 - q1) * (c2 - c1)
        if d == 0:
            continue
        bq = ((y2 - y1) * (c3 - c1) - (y3 - y1) * (c2 - c1)) / d
        bc = ((q2 - q1) * (y3 - y1) - (q3 - q1) * (y2 - y1)) / d
        a = y1 - bq * q1 - bc * c1
        res = max(abs(y - (a + bq * q + bc * c)) for q, c, y in pts)
        if best is None or res < best[0]:
            best = (res, a, bq, bc)
    res, a, bq, bc = best
    return a, bq, bc, res


# ---- unit checks (run at import; on synthetic data, never the answer) --------

def _unit_refit():
    pts = sweep_points()
    assert len(pts) == 9 and all(len(p) == 3 for p in pts)
    # minimax machinery on a synthetic exact line + one outlier: recovers
    # the line and reports the outlier as the residual
    xs = [Fraction(k, 4) for k in range(6)]
    ys = [2 + 3 * x for x in xs]
    ys[3] += Fraction(1, 10)
    best = None
    for i, j in combinations(range(6), 2):
        if xs[i] == xs[j]:
            continue
        b = (ys[j] - ys[i]) / (xs[j] - xs[i])
        a = ys[i] - b * xs[i]
        res = max(abs(y - (a + b * x)) for x, y in zip(xs, ys))
        if best is None or res < best[0]:
            best = (res, a, b)
    assert best[1] == 2 and best[2] == 3 and best[0] == Fraction(1, 10)


_unit_refit()


if __name__ == '__main__':
    a, b, res, n = minimax_affine()
    pa, pq, pc, pres = minimax_plane()
    print('claims/refit.py — machine refit over the frozen sweep '
          f'({n} rows), exact rational arithmetic:')
    print(f'  exact_fit over raw rows: '
          f'{"REFUSED (no exact law fits noise)" if exact_refusal() else "?!"}')
    print(f'  minimax affine:  L/w = {float(a):.4f} + {float(b):.4f} q'
          f'   (max |residual| {float(res):.4f})')
    print(f'  minimax plane:   L/w = {float(pa):.4f} + {float(pq):.4f} q '
          f'+ {float(pc):.4f} Ca   (max |residual| {float(pres):.4f})')
    print('  (what these numbers mean is the acceptance script\'s '
          'business — this module does not know)')
