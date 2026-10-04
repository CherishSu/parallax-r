"""Person A: check whether decisive claims cite existing evidence records.

Input judgments must first pass schema.validate_judgment. This module checks
reference existence, not whether a record logically supports the cited claim.
"""


def support(judgment, case):
    """Return U and auditable citation problems without changing the judgment."""
    claims = [claim for claim in judgment['claims'] if claim['critical']]
    events = {'POLICY'} | {event['event_id'] for event in case['events']}
    receipts = {receipt['receipt_id'] for receipt in case['receipts']}
    details = []
    for claim in claims:
        missing = not (claim['event_ids'] or claim['receipt_ids'])
        unknown_events = sorted(set(claim['event_ids']) - events)
        unknown_receipts = sorted(set(claim['receipt_ids']) - receipts)
        if missing or unknown_events or unknown_receipts:
            details.append({
                'claim_id': claim['claim_id'],
                'missing_references': missing,
                'unknown_event_ids': unknown_events,
                'unknown_receipt_ids': unknown_receipts,
            })
    return {
        'U': len(details) / len(claims) if claims else None,
        'unresolved_claims': [item['claim_id'] for item in details],
        'critical_claim_count': len(claims),
        'citation_issues': details,
        'semantic_support': 'NOT_CHECKED',
    }
