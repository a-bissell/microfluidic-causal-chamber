"""claims/audit.py — the mechanical audit of CLAIMS.md (port phase 2).

The registry is only worth keeping if a machine holds it to its own rules,
so this audit fails the tree when:

  * an entry uses a status outside the controlled vocabulary;
  * any [[link]] dangles (names no entry);
  * an entry depends on a refuted-frozen or withdrawn entry;
  * a battery-linked status (robust-/refuted-/downgraded-frozen) names no
    battery candidate, names an unknown one, or CONTRADICTS the battery's
    expected disposition — and, completeness, every battery candidate must
    be claimed by exactly one registry entry;
  * a refuted-frozen entry records no witness;
  * an assumption carries a verified: field (a verified assumption is a
    contradiction in terms);
  * an open entry names no distinguishing experiment;
  * a withdrawn entry neither points at a superseding entry nor says why;
  * a source: path does not exist in the repo;
  * the literal string TODO appears anywhere (claims are done or absent).

Query mode answers the question the registry exists for:

    python3 -m claims.audit --dependents sigma-30-assumed

prints the transitive closure of entries whose support falls if that
entry falls (the depends: edges, reversed).
"""
import re
import sys
from pathlib import Path

from claims import REPO

CLAIMS_MD = REPO / 'CLAIMS.md'

STATUSES = {'robust-frozen', 'refuted-frozen', 'downgraded-frozen',
            'prose-verified', 'assumption', 'open', 'withdrawn'}
BATTERY_STATUS = {'robust-frozen': 'SURVIVOR',
                  'refuted-frozen': 'REFUTED',
                  'downgraded-frozen': 'DOWNGRADED'}
_LINK = re.compile(r'\[\[([a-z0-9-]+)\]\]')
_FIELD = re.compile(r'^- ([a-z-]+):\s*(.*)$')


def parse(text):
    """{slug: entry} from registry markdown. Entries start at '### slug';
    '- key: value' lines are fields; depends edges come from the depends:
    field only, while links collects every [[x]] in the entry."""
    entries = {}
    for chunk in re.split(r'^### ', text, flags=re.M)[1:]:
        lines = chunk.splitlines()
        slug = lines[0].strip()
        e = dict(slug=slug, fields={}, body=chunk)
        for ln in lines[1:]:
            m = _FIELD.match(ln)
            if m:
                e['fields'][m.group(1)] = m.group(2).strip()
            elif ln.strip() and not ln.startswith('-'):
                break
        e['depends'] = _LINK.findall(e['fields'].get('depends', ''))
        e['links'] = _LINK.findall(chunk)
        entries[slug] = e
    return entries


def audit(entries, battery_expected, repo=REPO, full_text=''):
    """Returns a list of failure strings (empty = registry sound)."""
    fails = []
    claimed_battery = {}

    if 'TODO' in full_text:
        fails.append("stale-tag ban: literal 'TODO' present")

    for slug, e in entries.items():
        f = e['fields']
        status = f.get('status')
        if status not in STATUSES:
            fails.append(f'{slug}: unknown status {status!r}')
            continue
        for target in e['links']:
            if target not in entries:
                fails.append(f'{slug}: dangling link [[{target}]]')
        for dep in e['depends']:
            if entries.get(dep, {}).get('fields', {}).get('status') in (
                    'refuted-frozen', 'withdrawn'):
                fails.append(f'{slug}: depends on {dep} '
                             f'({entries[dep]["fields"]["status"]})')
        if status in BATTERY_STATUS:
            m = re.search(r'battery "([^"]+)"', f.get('verified', ''))
            if not m:
                fails.append(f'{slug}: {status} but verified: names no '
                             f'battery candidate')
            else:
                name = m.group(1)
                if name in claimed_battery:
                    fails.append(f'{slug}: battery candidate {name!r} '
                                 f'already claimed by '
                                 f'{claimed_battery[name]}')
                claimed_battery[name] = slug
                want = battery_expected.get(name)
                if want is None:
                    fails.append(f'{slug}: unknown battery candidate '
                                 f'{name!r}')
                elif want != BATTERY_STATUS[status]:
                    fails.append(f'{slug}: status {status} contradicts '
                                 f'battery expectation {want}')
        if status == 'refuted-frozen' and 'witness' not in e['body'].lower():
            fails.append(f'{slug}: refuted-frozen without a recorded witness')
        if status == 'assumption' and 'verified' in f:
            fails.append(f'{slug}: assumption with a verified: field')
        if status == 'open' and 'Distinguishing experiment' not in e['body']:
            fails.append(f'{slug}: open without a distinguishing experiment')
        if status == 'withdrawn':
            sup = f.get('superseded-by')
            if sup and sup not in entries:
                fails.append(f'{slug}: superseded-by unknown entry {sup!r}')
            if not sup and 'Withdrawn:' not in e['body']:
                fails.append(f'{slug}: withdrawn without superseded-by or '
                             f'a Withdrawn: line')
        if status == 'refuted-frozen':
            sup = f.get('superseded-by')
            if sup and sup not in entries:
                fails.append(f'{slug}: superseded-by unknown entry {sup!r}')
        src = f.get('source', '').split(' (')[0].strip()
        if not src:
            fails.append(f'{slug}: no source')
        elif not (repo / src).exists():
            fails.append(f'{slug}: source path does not exist: {src}')

    for name in battery_expected:
        if name not in claimed_battery:
            fails.append(f'battery candidate {name!r} has no registry entry')
    return fails


def dependents(entries, slug):
    """Transitive closure of entries whose depends: chain reaches slug."""
    rev = {}
    for s, e in entries.items():
        for dep in e['depends']:
            rev.setdefault(dep, []).append(s)
    out, stack = [], list(rev.get(slug, []))
    while stack:
        s = stack.pop()
        if s not in out:
            out.append(s)
            stack.extend(rev.get(s, []))
    return sorted(out)


# ---- unit checks (run at import; the audit's own failure modes) --------------

_GOOD = '''### a-claim
- status: robust-frozen
- kind: t
- source: CLAIMS.md
- verified: battery "cand A" (test)

Body.

### an-assumption
- status: assumption
- kind: t
- source: CLAIMS.md

Body.

### dependent-claim
- status: prose-verified
- kind: t
- source: CLAIMS.md
- depends: [[an-assumption]]

Body links [[a-claim]].
'''


def _unit_audit():
    exp = {'cand A': 'SURVIVOR'}
    entries = parse(_GOOD)
    assert audit(entries, exp, full_text=_GOOD) == []
    assert dependents(entries, 'an-assumption') == ['dependent-claim']
    bad_cases = (
        (_GOOD.replace('robust-frozen', 'certainly-true'), exp, 'unknown status'),
        (_GOOD.replace('[[a-claim]]', '[[no-such]]'), exp, 'dangling'),
        (_GOOD.replace('- status: assumption', '- status: withdrawn'), exp,
         'withdrawn without'),
        (_GOOD.replace('battery "cand A"', 'battery "cand B"'), exp, 'unknown battery'),
        (_GOOD, {'cand A': 'REFUTED'}, 'contradicts'),
        (_GOOD, dict(exp, **{'cand X': 'SURVIVOR'}), 'no registry entry'),
        (_GOOD.replace('- source: CLAIMS.md\n- verified',
                       '- source: nope.md\n- verified'), exp, 'does not exist'),
        (_GOOD + '\nTODO', exp, 'stale-tag'),
        (_GOOD.replace('- status: assumption',
                       '- status: assumption\n- verified: battery "x"'), exp,
         'assumption with'),
        (_GOOD.replace('depends: [[an-assumption]]', 'depends: [[bad-dep]]')
         .replace('### an-assumption\n- status: assumption',
                  '### bad-dep\n- status: withdrawn\n- superseded-by: a-claim'),
         exp, 'depends on bad-dep'),
    )
    for text, expected, needle in bad_cases:
        fails = audit(parse(text), expected, full_text=text)
        assert any(needle in f for f in fails), (needle, fails)


_unit_audit()


if __name__ == '__main__':
    from claims.battery import EXPECTED
    text = CLAIMS_MD.read_text()
    entries = parse(text)

    if len(sys.argv) == 3 and sys.argv[1] == '--dependents':
        slug = sys.argv[2]
        if slug not in entries:
            print(f'no such entry: {slug}')
            sys.exit(1)
        deps = dependents(entries, slug)
        print(f'if [[{slug}]] falls, so does support for '
              f'({len(deps)} entries):')
        for d in deps:
            print(f'  {d}  [{entries[d]["fields"]["status"]}]')
        sys.exit(0)

    fails = audit(entries, EXPECTED, full_text=text)
    by_status = {}
    for e in entries.values():
        by_status[e['fields'].get('status')] = \
            by_status.get(e['fields'].get('status'), 0) + 1
    print(f'CLAIMS.md: {len(entries)} entries '
          + str(dict(sorted(by_status.items()))))
    print(f'mechanization backlog (prose-verified): '
          f'{by_status.get("prose-verified", 0)}')
    if fails:
        print(f'\nAUDIT FAIL ({len(fails)}):')
        for f in fails:
            print(f'  {f}')
        sys.exit(1)
    print('AUDIT PASS (statuses controlled, links resolve, battery '
          'cross-check complete both ways, sources exist)')
    print("\nquery example:  python3 -m claims.audit --dependents "
          "sigma-30-assumed")
