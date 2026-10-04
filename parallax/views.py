"""Four deterministic presentations of one evidence packet (C/D)."""
import copy
import re
from .schema import digest


def alias_map(case):
    """Neutral labels numbered by first appearance, so numbering reveals nothing about later events."""
    aliases = {}
    for e in case['events']:
        aliases.setdefault(e['actor'], f'Actor {len(aliases) + 1}')
    return aliases


def mask_text(text, aliases):
    """Replace whole-word, case-insensitive occurrences of each known actor label in one pass."""
    if not aliases or not text:
        return text
    lookup = {a.lower(): alias for a, alias in aliases.items()}
    names = '|'.join(re.escape(a) for a in sorted(aliases, key=len, reverse=True))
    return re.sub(rf'(?<!\w)(?:{names})(?!\w)', lambda m: lookup[m.group(0).lower()], text, flags=re.IGNORECASE)


def render(case, report, name):
    if name not in ('full', 'action_only', 'masked', 'ledger'):
        raise ValueError('Unknown view')
    # Canonical events remain present; actor identity is a display label only.
    evidence = dict(task=case['task'], policy={'event_id': 'POLICY', 'text': case['policy']},
                    events=copy.deepcopy(case['events']), receipts=copy.deepcopy(case['receipts']), reconciliation=copy.deepcopy(report))
    aliases = alias_map(case)
    if name == 'masked':
        for e in evidence['events']:
            e['actor'] = aliases[e['actor']]
    narrative = case['narrative'] if name in ('full', 'masked') else ''
    if name == 'masked':
        narrative = mask_text(narrative, aliases)
    payload = dict(evidence=evidence, explanation=narrative)
    if name == 'ledger':
        # Same evidence, chronological tabular-style JSON formatting; no extra facts.
        payload['presentation'] = 'Read events in listed order as an evidence ledger.'
    return {'name': name, 'payload': payload, 'hash': digest(payload)}


def masking_residue(case):
    """Audit: where do actor names still appear in what the masked view would show the reviewer?

    EXACT   = a full actor label survives (should not happen after masking; indicates a masker bug).
    IN_*    = the label appears in task/policy/event fields, which masking deliberately leaves alone
              because changing them could alter policy facts. A human must decide whether identity
              determines permission; if so the case should be excluded from identity comparisons.
    PARTIAL = the last word of a multi-word label (for example a surname) appears alone, which the
              exact-label masker does not catch. Edit the narrative to use the full label, or exclude.
    This audit does not exclude anything by itself: the primary full/action-only comparison does not
    depend on the masked view (PRE-REGISTRATION.md section 4/METRICS section 2).
    """
    aliases = alias_map(case)
    masked = render(case, {'findings': [], 'coverage': case['coverage']}, 'masked')['payload']
    fields = {'narrative': masked['explanation'], 'task': masked['evidence']['task'], 'policy': masked['evidence']['policy']['text']}
    for e in masked['evidence']['events']:
        for key in ('operation', 'resource', 'output'):
            fields[f"event {e['event_id']} {key}"] = e[key]
    found = []
    for actor in aliases:
        full = re.compile(rf'(?<!\w){re.escape(actor)}(?!\w)', re.IGNORECASE)
        words = actor.split()
        partial = re.compile(rf'(?<!\w){re.escape(words[-1])}(?!\w)', re.IGNORECASE) if len(words) > 1 and len(words[-1]) >= 3 else None
        for where, text in fields.items():
            if full.search(text):
                found.append({'actor': actor, 'where': where, 'kind': 'EXACT' if where == 'narrative' else 'IN_' + where.split()[0].upper()})
            elif partial and partial.search(text):
                found.append({'actor': actor, 'where': where, 'kind': 'PARTIAL'})
    return found


def check_invariants(case, report, views):
    expected = render(case, report, 'full')['payload']['evidence']
    aliases = alias_map(case)
    for view in views:
        actual = copy.deepcopy(view['payload']['evidence'])
        baseline = copy.deepcopy(expected)
        # Only the masked view may alter actor display labels, and only by a consistent one-to-one relabeling.
        if view['name'] == 'masked':
            seen = {}
            for shown, original in zip(actual['events'], baseline['events']):
                if seen.setdefault(original['actor'], shown['actor']) != shown['actor']:
                    raise ValueError('Masked view relabels one actor inconsistently')
            if len(set(seen.values())) != len(seen):
                raise ValueError('Masked view merges distinct actors')
            for obj in (actual, baseline):
                for e in obj['events']:
                    e.pop('actor')
        if actual != baseline:
            raise ValueError(f"Evidence changed in {view['name']}")
        if digest(view['payload']) != view['hash']:
            raise ValueError('View hash mismatch')
    return True
