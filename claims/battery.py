"""claims/battery.py — the frozen-data claims battery (phase 1 of the port).

Every claim the results/*/README.md files state in prose — plus two posed
by this battery — expressed as ready-made conjectures (conjecture_spec, the
engine's zero-plug path) and pushed through lakatos.run_engine: derived
attack schedule, graded verdict, envelope, witness on every kill.

What this battery is FOR, beyond regression:

  * The SUPERSEDED mill3d_2026-07 verdict is re-derived MECHANICALLY: the
    originally-reported 2D->3D correction (x2.4 frequency, x1.43 speed)
    dies against the corrected mill3d800 data with a witness, instead of
    living only in a README warning box.
  * The corrected correction factors are graded DOWNGRADED, not robust:
    they rest on ONE matched pair, and the signature says so. Promoting
    them means new solves (phase 4), not prose.
  * Two kills localize the same anomaly: droplet speed breaks monotonicity
    at (P_cont 10 kPa, P_disp 3.3->3.6 kPa), and the protocol-vs-psweep
    cross-run disagreement peaks (6.8%) at (13 kPa, 3.6 kPa) — both in the
    P_disp = 3.6 kPa column the psweep5x5 README already flagged as
    "regime-boundary-adjacent" (suspected period-doubling). The refuter's
    witnesses turn that suspicion into named coordinates.

Run from the repo root:  python3 -m claims.battery
"""
import sys
from fractions import Fraction

from lakatos import Axis, EngineCandidate, run_engine

from claims import frozen, refit


def candidates():
    cands = []
    grid_axes = [Axis('nc', lo=1), Axis('nd', lo=1)]
    grid_ok = lambda nc, nd: 1 <= nc <= 5 and 1 <= nd <= 5
    grid_cost = lambda nc, nd: nc * nd

    # -- psweep5x5: L/w monotone in both actuators (README line "monotonic
    # in both actuators across all 25 cells")
    t, _, _ = frozen.grid_monotone_test(
        frozen.PSWEEP, 'P_cont_nominal', 'P_disp_nominal', 'L_over_w',
        along_d='inc', along_c='dec')
    cands.append(EngineCandidate(
        'psweep5x5: L/w monotone in both actuators',
        'results/psweep5x5_2026-07/README.md',
        conjecture_spec=dict(
            claim='cell-mean L/w strictly increases with P_disp and strictly '
                  'decreases with P_cont over the committed 5x5 grid',
            instance=t, axes=grid_axes, inspiring=[(2, 2)],
            valid=grid_ok, cost=grid_cost, cap=100)))

    # -- psweep5x5: the whole actuator window produces droplets
    t, _, _ = frozen.grid_regime_test(
        frozen.PSWEEP, 'P_cont_nominal', 'P_disp_nominal', 'status', {'ok'})
    cands.append(EngineCandidate(
        'psweep5x5: droplets in every cell (window open)',
        'results/psweep5x5_2026-07/README.md',
        conjecture_spec=dict(
            claim='all 75 committed runs completed with droplets (status ok)',
            instance=t, axes=grid_axes, inspiring=[(2, 2)],
            valid=grid_ok, cost=grid_cost, cap=100)))

    # -- window600: same two claims at 600 um, +/-30% window
    t, _, _ = frozen.grid_monotone_test(
        frozen.WINDOW600, 'P_cont_Pa', 'P_disp_Pa', 'L_over_w',
        along_d='inc', along_c='dec')
    cands.append(EngineCandidate(
        'window600: L/w monotone in both actuators',
        'results/window600_2026-07/README.md ("monotonic in 25/25 cells")',
        conjecture_spec=dict(
            claim='L/w strictly increases with P_disp and decreases with '
                  'P_cont over the +/-30% window at 600 um',
            instance=t, axes=grid_axes, inspiring=[(2, 2)],
            valid=grid_ok, cost=grid_cost, cap=100)))
    t, _, _ = frozen.grid_regime_test(
        frozen.WINDOW600, 'P_cont_Pa', 'P_disp_Pa', 'verdict', {'drips'})
    cands.append(EngineCandidate(
        'window600: drips in every cell (window at least +/-30%)',
        'results/window600_2026-07/README.md',
        conjecture_spec=dict(
            claim='every cell of the +/-30% window at 600 um drips',
            instance=t, axes=grid_axes, inspiring=[(2, 2)],
            valid=grid_ok, cost=grid_cost, cap=100)))

    # -- POSED BY THIS BATTERY: the symmetric-sounding speed claim. L/w is
    # monotone in both actuators; is advection speed? (Expected: killed.)
    t, _, _ = frozen.grid_monotone_test(
        frozen.PSWEEP, 'P_cont_nominal', 'P_disp_nominal', 'v_drop_mm_s',
        along_d='inc', along_c='inc')
    cands.append(EngineCandidate(
        'psweep5x5: droplet speed monotone in both actuators',
        'posed by this battery (plausible by symmetry with L/w)',
        conjecture_spec=dict(
            claim='cell-mean droplet speed strictly increases with both '
                  'actuators over the committed grid',
            instance=t, axes=grid_axes, inspiring=[(2, 2)],
            valid=grid_ok, cost=grid_cost, cap=100)))

    # -- plan 7.1: measurement-noise conditional independence
    t, ncells = frozen.noise_independence_test()
    cands.append(EngineCandidate(
        'psweep5x5: actuator measurement noises independent',
        'hardware/microfluidic/microfluidic_chamber_plan.md sec. 7.1',
        conjecture_spec=dict(
            claim='P_cont_meas and P_disp_meas residuals (given the nominal '
                  'cell) are uncorrelated: |r| <= 3/sqrt(n)',
            instance=t, axes=[Axis('k', lo=2)], inspiring=[(10,)],
            valid=lambda k: 2 <= k <= ncells, cost=lambda k: 3 * k,
            cap=200)))

    # -- scaleup: similarity within 4%, out-of-sample from the 400 um anchor
    t, nw = frozen.scaleup_similarity_test(tol=0.04)
    cands.append(EngineCandidate(
        'scaleup: similarity within 4% (400 um anchor predicts 600/800)',
        'results/scaleup_2026-07/README.md ("similarity holds to within 4%")',
        conjecture_spec=dict(
            claim='L ~ w, L/w and speed flat, period ~ w, f ~ 1/w, Q ~ w^2, '
                  'V ~ w^3, each within 4% of the 400 um prediction',
            instance=t, axes=[Axis('nw', lo=1)], inspiring=[(2,)],
            valid=lambda k: 1 <= k <= nw, cost=lambda k: 8 * k, cap=100)))

    # -- Tier-0 identity: V_drop = Q_water x period (pipeline mass balance)
    t, nw = frozen.volume_consistency_test(tol=0.01)
    cands.append(EngineCandidate(
        'scaleup: V_drop = Q_water x period within 1%',
        'results/scaleup_2026-07/README.md (mass-conservation self-check)',
        conjecture_spec=dict(
            claim='measured droplet volume equals dispersed flux x period '
                  'at every committed width',
            instance=t, axes=[Axis('nw', lo=1)], inspiring=[(2,)],
            valid=lambda k: 1 <= k <= nw, cost=lambda k: k, cap=100)))

    # -- the SUPERSEDED 2D->3D correction, exactly as first reported: must
    # die against the corrected matched-pair data (mechanical re-derivation
    # of the README's warning box)
    pair_axes = [Axis('pair', lo=1)]
    pair_ok = lambda p: p == 1
    t = frozen.mill_ratio_test(
        dict(L_um=1.03, speed_mm_s=1.43, f_Hz=2.4), tol=0.05)
    cands.append(EngineCandidate(
        'mill3d: 2D->3D correction as FIRST reported (superseded)',
        'results/mill3d_2026-07/README.md (original claim, later withdrawn)',
        conjecture_spec=dict(
            claim='3D/2D at the matched point: length +3%, speed x1.43, '
                  'frequency x2.4',
            instance=t, axes=pair_axes, inspiring=[(1,)],
            valid=pair_ok, cost=lambda p: 3, cap=10)))

    # -- the corrected factors: hold, but rest on ONE matched pair
    t = frozen.mill_ratio_test(
        dict(L_um=0.87, speed_mm_s=1.17, f_Hz=1.59), tol=0.05)
    cands.append(EngineCandidate(
        'mill3d800: corrected 2D->3D factors (x0.87 L, x1.17 v, x1.59 f)',
        'results/mill3d800_2026-08/README.md',
        conjecture_spec=dict(
            claim='3D/2D at the matched 800 um point: length x0.87, speed '
                  'x1.17, droplet rate x1.59',
            instance=t, axes=pair_axes, inspiring=[(1,)],
            valid=pair_ok, cost=lambda p: 3, cap=10)))

    # -- POSED BY THIS BATTERY: cross-run reproducibility, strong and weak
    # forms, between two independent frozen runs at shared settings
    t, nshared = frozen.cross_repro_test(tol=0.05, mode='pointwise')
    cands.append(EngineCandidate(
        'protocol vs psweep: L/w agrees within 5% at EVERY shared setting',
        'posed by this battery (inspired by protocol_v1 README cross-check)',
        conjecture_spec=dict(
            claim='the protocol run and the cold-start grid agree pointwise '
                  'within 5% on L/w at all shared settings',
            instance=t, axes=[Axis('k', lo=1)], inspiring=[(2,)],
            valid=lambda k: 1 <= k <= nshared, cost=lambda k: k, cap=100)))
    # -- phase 3: the machine-refit scaling law as a permanent fixture.
    # The law's coefficients come from claims/refit.py (minimax support-pair
    # refit, exact rational, no-hints-guarded); whether they match the
    # published literature form is refit_acceptance.py's R3. Here the claim
    # is data-internal: the machine law holds within its declared tolerance
    # over every frozen sweep row.
    a, b, _res, nrows = refit.minimax_affine()
    spts = sorted(refit.sweep_points())
    tol = Fraction('0.11')

    def refit_instance(k):
        for q, _, y in spts[:k]:
            if abs(y - (a + b * q)) > tol:
                return False, dict(q=float(q), got=float(y),
                                   law=round(float(a + b * q), 4)), k
        return True, None, k

    cands.append(EngineCandidate(
        'sweep: L/w affine in flow-rate ratio (machine-refit law)',
        'claims/refit.py (minimax refit; matched to literature by '
        'refit_acceptance.py)',
        conjecture_spec=dict(
            claim='the machine-refit affine law holds within 0.11 on L/w '
                  'over every frozen velocity-sweep row',
            instance=refit_instance, axes=[Axis('k', lo=2)],
            inspiring=[(3,)], valid=lambda k: 2 <= k <= nrows,
            cost=lambda k: k, cap=100)))

    t, nshared = frozen.cross_repro_test(tol=0.03, mode='median')
    cands.append(EngineCandidate(
        'protocol vs psweep: median L/w disagreement within 3%',
        'posed by this battery (inspired by protocol_v1 README cross-check)',
        conjecture_spec=dict(
            claim='the median relative L/w disagreement across shared '
                  'settings stays within 3%',
            instance=t, axes=[Axis('k', lo=1)], inspiring=[(2,)],
            valid=lambda k: 1 <= k <= nshared, cost=lambda k: k, cap=100)))

    return cands


EXPECTED = {
    'psweep5x5: L/w monotone in both actuators': 'SURVIVOR',
    'psweep5x5: droplets in every cell (window open)': 'SURVIVOR',
    'window600: L/w monotone in both actuators': 'SURVIVOR',
    'window600: drips in every cell (window at least +/-30%)': 'SURVIVOR',
    'psweep5x5: droplet speed monotone in both actuators': 'REFUTED',
    'psweep5x5: actuator measurement noises independent': 'SURVIVOR',
    'scaleup: similarity within 4% (400 um anchor predicts 600/800)':
        'SURVIVOR',
    'scaleup: V_drop = Q_water x period within 1%': 'SURVIVOR',
    'mill3d: 2D->3D correction as FIRST reported (superseded)': 'REFUTED',
    'mill3d800: corrected 2D->3D factors (x0.87 L, x1.17 v, x1.59 f)':
        'DOWNGRADED',
    'protocol vs psweep: L/w agrees within 5% at EVERY shared setting':
        'REFUTED',
    'protocol vs psweep: median L/w disagreement within 3%': 'SURVIVOR',
    'sweep: L/w affine in flow-rate ratio (machine-refit law)': 'SURVIVOR',
}


if __name__ == '__main__':
    print('================ FROZEN-DATA CLAIMS BATTERY '
          '(doubles as acceptance ledger) ================')
    out = run_engine(candidates())

    print('\n---- acceptance ----')
    got = {r['name']: r['disposition'] for r in out['rows']}
    details = {r['name']: r for r in out['rows']}
    all_ok = True
    for name, want in EXPECTED.items():
        ok = got.get(name) == want
        all_ok &= ok
        print(f"  {'PASS' if ok else 'FAIL'}  {name}: {got.get(name)} "
              f"(expected {want})")

    # witness spot-checks: the two kills must localize the 3.6 kPa column
    speed = details['psweep5x5: droplet speed monotone in both actuators']
    w_ok = '3600' in speed['detail'] and '3300' in speed['detail']
    all_ok &= w_ok
    print(f"  {'PASS' if w_ok else 'FAIL'}  speed kill names the "
          f"(3300 -> 3600 Pa) pair")
    cross = details['protocol vs psweep: L/w agrees within 5% at EVERY '
                    'shared setting']
    c_ok = '13000' in cross['detail'] and '3600' in cross['detail']
    all_ok &= c_ok
    print(f"  {'PASS' if c_ok else 'FAIL'}  cross-run kill names the "
          f"(13000, 3600) setting")

    print(f"\nCLAIMS BATTERY {'PASS' if all_ok else 'FAIL'} "
          f"({out['cases']} frozen cases re-checked, {out['elapsed']:.1f}s)")
    sys.exit(0 if all_ok else 1)
