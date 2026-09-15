"""claims/refit_acceptance.py — did the machine re-derive Garstecki unaided?

Port phase 3, the checker side — the analogue of the engine's t25: the
fitter (claims/refit.py) proposes a law knowing nothing; THIS script knows
the published answer (Garstecki 2006 squeezing-regime form, recovered by
the project as L/w = 0.80 + 1.24 q, R^2 = 0.94 — see
results/sweep_2026-07/README.md) and judges the proposal.

  R1  no-hints guard: the fit path's sources (claims/refit.py,
      claims/frozen.py, lakatos/fitter.py) contain none of the banned
      tokens — the law's name, its published coefficients, the repo's
      validation script, or any least-squares vocabulary. Mechanically
      enforced, not promised.
  R2  honest refusal: the exact fitter REFUSED the raw noisy rows.
  R3  unaided recovery: the minimax refit's slope and intercept land
      within 10% of the published 1.24 and 0.80.
  R4  bounded residual: max |residual| of the machine law <= 0.11 over
      all 9 frozen rows (the battery re-checks this claim every run).
  R5  Ca-stratification rediscovered: adding the capillary number as a
      second atom tightens the minimax residual by at least 2x with a
      NEGATIVE Ca coefficient — the machine's version of the README's
      "shear-assisted breakup shortens slugs" note, derived blind.
"""
import sys
from pathlib import Path

import lakatos.fitter

from claims import refit

PUB_INTERCEPT, PUB_SLOPE = 0.80, 1.24
BAND = 0.10                    # relative band for R3
RESIDUAL_TOL = 0.11            # R4 bound; also the battery claim's tol

BANNED = ('garstecki', '1.24', '0.80', '1.2406', '0.8015',
          'least_squares', 'lstsq', 'polyfit', 'validate_')

FIT_PATH_SOURCES = (
    Path(refit.__file__),
    Path(refit.__file__).with_name('frozen.py'),
    Path(lakatos.fitter.__file__),
)


def run():
    checks = []

    src = '\n'.join(p.read_text() for p in FIT_PATH_SOURCES).lower()
    hits = [t for t in BANNED if t in src]
    checks.append(('R1 no-hints guard over the fit path', not hits,
                   f'banned tokens present: {hits}' if hits else
                   f'{len(FIT_PATH_SOURCES)} sources clean'))

    refused = refit.exact_refusal()
    checks.append(('R2 exact fitter refuses raw noisy rows', refused,
                   'refused (honest)' if refused else
                   'produced an exact fit on noise?!'))

    a, b, res, n = refit.minimax_affine()
    da = abs(float(a) / PUB_INTERCEPT - 1)
    db = abs(float(b) / PUB_SLOPE - 1)
    checks.append((f'R3 unaided recovery within {BAND:.0%}',
                   da <= BAND and db <= BAND,
                   f'machine L/w = {float(a):.4f} + {float(b):.4f} q vs '
                   f'published {PUB_INTERCEPT} + {PUB_SLOPE} q '
                   f'(intercept off {da:.1%}, slope off {db:.1%})'))

    checks.append((f'R4 max |residual| <= {RESIDUAL_TOL}',
                   float(res) <= RESIDUAL_TOL,
                   f'{float(res):.4f} over {n} rows'))

    pa, pq, pc, pres = refit.minimax_plane()
    improve = float(res) / float(pres)
    checks.append(('R5 Ca-stratification rediscovered (>=2x tighter, '
                   'negative coefficient)',
                   improve >= 2.0 and pc < 0,
                   f'plane residual {float(pres):.4f} ({improve:.1f}x '
                   f'tighter), Ca coefficient {float(pc):.2f}'))

    all_ok = True
    for name, ok, detail in checks:
        all_ok &= ok
        print(f"  {'PASS' if ok else 'FAIL'}  {name}: {detail}")
    return all_ok


if __name__ == '__main__':
    print('================ REFIT ACCEPTANCE (phase 3: the port\'s t25) '
          '================')
    ok = run()
    print(f"\nREFIT ACCEPTANCE {'PASS' if ok else 'FAIL'} — the machine "
          f"{'re-derived the published scaling law unaided' if ok else 'did NOT meet the acceptance bands'}")
    sys.exit(0 if ok else 1)
