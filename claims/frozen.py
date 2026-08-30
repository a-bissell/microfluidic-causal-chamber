"""claims/frozen.py — the Tier-1 decider: exhaustive checks over frozen CSVs.

Every instance test here returns the engine's universal triple

    (holds: bool, witness: Any|None, n_cases: int)

evaluated EXHAUSTIVELY over the committed rows it declares — the harness
decides, never a narrative. The parameterization convention for grid data
is prefix counts over the sorted actuator levels: an instance (nc, nd)
covers the first nc P_cont levels x the first nd P_disp levels, so
"inspiring" = the small pilot corner and the derived schedule escalates to
the full committed grid (the claim's envelope). n_cases counts CSV rows
actually examined, so the engine's case accounting stays honest.

Data files are read once at import and cached; all parsing is stdlib csv.
"""
import csv
import math
import statistics as st
from itertools import product

from claims import RESULTS


# ---- loading -----------------------------------------------------------------

def _read(relpath):
    with open(RESULTS / relpath, newline='') as f:
        return list(csv.DictReader(f))


def _cells(rows, kc, kd, kv):
    """{(P_cont, P_disp): [values across repeats]} from long-format rows."""
    out = {}
    for r in rows:
        out.setdefault((float(r[kc]), float(r[kd])), []).append(float(r[kv]))
    return out


PSWEEP = _read('psweep5x5_2026-07/results.csv')
PSWEEP_CAUSAL = _read('psweep5x5_2026-07/causal_dataset.csv')
WINDOW600 = _read('window600_2026-07/window_results.csv')
SCALEUP = _read('scaleup_2026-07/summary.csv')
MILL3D800 = _read('mill3d800_2026-08/metrics.csv')
PROTOCOL = _read('protocol_v1_2026-07/protocol_results.csv')
SWEEP = _read('sweep_2026-07/sweep_results.csv')


# ---- grid monotonicity -------------------------------------------------------

def grid_monotone_test(rows, kc, kd, kv, along_d='inc', along_c='dec'):
    """Instance test (nc, nd): cell means of kv are strictly monotone along
    each included P_disp row ('inc'/'dec' per along_d) and each included
    P_cont column (along_c). Witness = the first violating adjacent pair."""
    cells = _cells(rows, kc, kd, kv)
    pcs = sorted({k[0] for k in cells})
    pds = sorted({k[1] for k in cells})
    mean = {k: st.mean(v) for k, v in cells.items()}

    def ordered(a, b, sense):
        return b > a if sense == 'inc' else b < a

    def test(nc, nd):
        sc, sd = pcs[:nc], pds[:nd]
        n = sum(len(cells[(c, d)]) for c, d in product(sc, sd))
        for c in sc:
            for d1, d2 in zip(sd, sd[1:]):
                if not ordered(mean[(c, d1)], mean[(c, d2)], along_d):
                    return False, dict(axis='P_disp', at_P_cont=c,
                                       pair=(d1, d2), sense=along_d,
                                       values=(round(mean[(c, d1)], 3),
                                               round(mean[(c, d2)], 3))), n
        for d in sd:
            for c1, c2 in zip(sc, sc[1:]):
                if not ordered(mean[(c1, d)], mean[(c2, d)], along_c):
                    return False, dict(axis='P_cont', at_P_disp=d,
                                       pair=(c1, c2), sense=along_c,
                                       values=(round(mean[(c1, d)], 3),
                                               round(mean[(c2, d)], 3))), n
        return True, None, n

    return test, len(pcs), len(pds)


def grid_regime_test(rows, kc, kd, kregime, allowed):
    """Instance test (nc, nd): every included row's regime/verdict is in
    `allowed` (droplets form across the whole included window)."""
    pcs = sorted({float(r[kc]) for r in rows})
    pds = sorted({float(r[kd]) for r in rows})

    def test(nc, nd):
        sc, sd = set(pcs[:nc]), set(pds[:nd])
        n = 0
        for r in rows:
            if float(r[kc]) in sc and float(r[kd]) in sd:
                n += 1
                if r[kregime] not in allowed:
                    return False, dict(P_cont=float(r[kc]),
                                       P_disp=float(r[kd]),
                                       got=r[kregime]), n
        return True, None, n

    return test, len(pcs), len(pds)


# ---- conditional independence of measurement noise ---------------------------

def noise_independence_test():
    """Instance test (k,): over the first k cells of the causal dataset,
    the measurement residuals (P_meas - P_nominal) of the two actuators are
    uncorrelated: |r| <= 3/sqrt(n_rows). This is plan section 7.1's
    'P_cont_meas independent of P_disp_meas given P_cont, P_disp' on the
    frozen interventional grid (conditioning on the cell = using nominal
    residuals)."""
    by_cell = {}
    for r in PSWEEP_CAUSAL:
        by_cell.setdefault((float(r['P_cont']), float(r['P_disp'])),
                           []).append(r)
    order = sorted(by_cell)

    def test(k):
        rows = [r for cell in order[:k] for r in by_cell[cell]]
        rc = [float(r['P_cont_meas']) - float(r['P_cont']) for r in rows]
        rd = [float(r['P_disp_meas']) - float(r['P_disp']) for r in rows]
        n = len(rows)
        mc, md = st.mean(rc), st.mean(rd)
        num = sum((a - mc) * (b - md) for a, b in zip(rc, rd))
        den = math.sqrt(sum((a - mc) ** 2 for a in rc)
                        * sum((b - md) ** 2 for b in rd))
        r_ = num / den if den else 0.0
        thr = 3 / math.sqrt(n)
        ok = abs(r_) <= thr
        return ok, (None if ok else dict(r=round(r_, 4),
                                         threshold=round(thr, 4), n=n)), n

    return test, len(order)


# ---- scale-up similarity and volume consistency ------------------------------

_SCALEUP_OBS = (          # column, exponent p in  x(w) = x(400) * (w/400)^p
    ('L_um', 1), ('L_over_w', 0), ('speed_mm_s', 0), ('period_s', 1),
    ('f_Hz', -1), ('Q_oil_uL_s', 2), ('Q_water_uL_s', 2), ('V_drop_nL', 3),
)


def scaleup_similarity_test(tol=0.04):
    """Instance test (nw,): the first nw widths' observables match the
    similarity prediction from the 400 um anchor within tol. 600 and 800
    are out-of-sample predictions, not fits (the anchor is row 0)."""
    rows = sorted(SCALEUP, key=lambda r: float(r['w_um']))
    anchor = rows[0]
    w0 = float(anchor['w_um'])

    def test(nw):
        n = 0
        for r in rows[:nw]:
            ratio = float(r['w_um']) / w0
            for col, p in _SCALEUP_OBS:
                n += 1
                pred = float(anchor[col]) * ratio ** p
                got = float(r[col])
                if abs(got / pred - 1) > tol:
                    return False, dict(w_um=float(r['w_um']), obs=col,
                                       got=got, predicted=round(pred, 4),
                                       err_pct=round((got / pred - 1) * 100,
                                                     2)), n
        return True, None, n

    return test, len(rows)


def volume_consistency_test(tol=0.01):
    """Instance test (nw,): V_drop equals Q_water x period within tol —
    the pipeline's mass-conservation self-check as a regression fixture."""
    rows = sorted(SCALEUP, key=lambda r: float(r['w_um']))

    def test(nw):
        n = 0
        for r in rows[:nw]:
            n += 1
            v = float(r['V_drop_nL'])
            pred = float(r['Q_water_uL_s']) * float(r['period_s']) * 1e3
            if abs(pred / v - 1) > tol:
                return False, dict(w_um=float(r['w_um']), V_nL=v,
                                   Q_x_period_nL=round(pred, 2)), n
        return True, None, n

    return test, len(rows)


# ---- the 2D->3D correction factors (mill3d800 matched pair) ------------------

def mill_ratio_test(claimed, tol=0.05):
    """Instance test (pair,): the 3D/2D ratios of the matched mill3d800
    pair match `claimed` = {metric: ratio} within tol. There is exactly ONE
    matched pair in the frozen data — the signature says so (valid: pair==1),
    and the refuter will grade accordingly (nothing beyond inspiring)."""
    d2 = next(r for r in MILL3D800 if r['dim'] == '2D')
    d3 = next(r for r in MILL3D800 if r['dim'] == '3D')

    def test(pair):
        n = 0
        for col, want in claimed.items():
            n += 1
            got = float(d3[col]) / float(d2[col])
            if abs(got / want - 1) > tol:
                return False, dict(metric=col, claimed_ratio=want,
                                   measured_ratio=round(got, 3)), n
        return True, None, n

    return test


# ---- cross-run reproducibility (protocol_v1 vs psweep5x5) --------------------

def cross_repro_test(tol, mode):
    """Instance test (k,): over the first k settings shared between the
    protocol_v1 run and the cold-start psweep5x5 grid, the relative L/w
    disagreement is within tol — 'pointwise' (every setting) or 'median'.
    Two INDEPENDENT frozen runs at the same nominal settings."""
    prot = _cells(PROTOCOL, 'P_cont', 'P_disp', 'L_over_w')
    grid = _cells(PSWEEP, 'P_cont_nominal', 'P_disp_nominal', 'L_over_w')
    shared = sorted(set(prot) & set(grid))

    def test(k):
        pairs = shared[:k]
        n = sum(len(prot[s]) + len(grid[s]) for s in pairs)
        diffs = []
        for s in pairs:
            d = abs(st.mean(prot[s]) - st.mean(grid[s])) / st.mean(grid[s])
            diffs.append((d, s))
            if mode == 'pointwise' and d > tol:
                return False, dict(setting=s, rel_diff_pct=round(d * 100, 2),
                                   tol_pct=tol * 100), n
        if mode == 'median' and st.median(d for d, _ in diffs) > tol:
            worst = max(diffs)
            return False, dict(median_pct=round(
                st.median(d for d, _ in diffs) * 100, 2),
                worst=worst[1], tol_pct=tol * 100), n
        return True, None, n

    return test, len(shared)


# ---- unit checks (run at import, engine convention) --------------------------

def _unit_frozen():
    toy = [dict(c=str(c), d=str(d), v=str(c * 10 + d))
           for c in (1, 2) for d in (1, 2)]
    t, nc, nd = grid_monotone_test(toy, 'c', 'd', 'v',
                                   along_d='inc', along_c='inc')
    ok, w, n = t(2, 2)
    assert ok and w is None and n == 4 and (nc, nd) == (2, 2)
    t, _, _ = grid_monotone_test(toy, 'c', 'd', 'v',
                                 along_d='dec', along_c='inc')
    ok, w, n = t(2, 2)
    assert not ok and w['axis'] == 'P_disp' and n == 4
    # frozen files loaded and shaped as expected
    assert len(PSWEEP) == 75 and len(PSWEEP_CAUSAL) == 75
    assert len(WINDOW600) == 25 and len(SCALEUP) == 3 and len(MILL3D800) == 2
    assert len(SWEEP) == 11


_unit_frozen()


if __name__ == '__main__':
    print('claims/frozen.py unit checks: PASS (monotone helper, frozen-file '
          'shapes: psweep 75, window 25, scaleup 3, mill3d800 2, protocol '
          f'{len(PROTOCOL)} segments)')
