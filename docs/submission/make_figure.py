"""Draw the submission figure from a saved walkthrough run (no model calls).

Usage: python3 docs/submission/make_figure.py output/walkthrough/results.json
"""
import collections
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent
VIEWS = [('full', 'Full'), ('action_only', 'Action\nonly'), ('masked', 'Masked'), ('ledger', 'Ledger')]
REASONS = ['VIEW_FRAGILITY', 'EVIDENCE_CONFLICT', 'INCOMPLETE_RECORD', 'UNSUPPORTED_CLAIM',
           'MONITOR_ABSTENTION', 'VIEW_VALIDATION_FAILURE']
PROHIBITED, ALLOWED = '#2a78d6', '#eb6834'
INK, MUTED, GRID = '#0b0b0b', '#52514e', '#e4e3df'


def main(path):
    run = json.loads(Path(path).read_text(encoding='utf-8'))
    detection = run['summary']['detection']
    reasons = collections.Counter()
    for result in run['results']:
        reasons.update(result['metrics']['decision']['reason_codes'])
    accepted = sum(r['metrics']['decision']['action'] == 'ACCEPT' for r in run['results'])

    plt.rcParams.update({'font.family': 'serif', 'font.size': 8.5, 'axes.edgecolor': MUTED,
                         'axes.labelcolor': INK, 'xtick.color': MUTED, 'ytick.color': MUTED})
    fig, (a, b) = plt.subplots(1, 2, figsize=(6.6, 2.55), gridspec_kw={'width_ratios': [1.05, 1]})

    width, x = 0.36, range(len(VIEWS))
    for offset, cls, color, label in ((-width / 2 - 0.01, 'harmful', PROHIBITED, 'Prohibited (n=10)'),
                                      (width / 2 + 0.01, 'benign', ALLOWED, 'Allowed (n=10)')):
        values = [detection[v][cls]['flagged'] for v, _ in VIEWS]
        bars = a.bar([i + offset for i in x], values, width, color=color, label=label, zorder=3)
        for bar, value in zip(bars, values):
            a.text(bar.get_x() + bar.get_width() / 2, value + 0.25, str(value), ha='center', va='bottom',
                   fontsize=7.5, color=INK)
    a.set_xticks(list(x), [name for _, name in VIEWS])
    a.set_ylim(0, 14)
    a.set_yticks([0, 5, 10])
    a.set_ylabel('Cases flagged (majority of 3)')
    a.set_title('(a) FLAG verdicts by view', fontsize=9, loc='left')
    a.legend(frameon=False, fontsize=7.5, loc='upper left', ncol=2, bbox_to_anchor=(0.0, 1.02), handlelength=1.2, columnspacing=1.0)
    a.grid(axis='y', color=GRID, zorder=0)

    labels = REASONS + ['ACCEPT (no reason)']
    counts = [reasons.get(r, 0) for r in REASONS] + [accepted]
    y = list(range(len(labels)))[::-1]
    b.barh(y, counts, 0.6, color=[PROHIBITED] * len(REASONS) + [MUTED], zorder=3)
    for yi, count in zip(y, counts):
        b.text(count + 0.3, yi, str(count), va='center', fontsize=7.5, color=INK)
    b.set_yticks(y, [label.replace('_', ' ').title().replace('(No Reason)', '(no reason)') for label in labels],
                 fontsize=7.5)
    b.set_xlim(0, 16.5)
    b.set_xlabel(f"Cases (of {len(run['results'])})")
    b.set_title('(b) Gate outcomes across all cases', fontsize=9, loc='left')
    b.grid(axis='x', color=GRID, zorder=0)

    for ax in (a, b):
        for side in ('top', 'right'):
            ax.spines[side].set_visible(False)
    fig.tight_layout()
    fig.savefig(HERE / 'figure1.pdf')
    fig.savefig(HERE / 'figure1.png', dpi=200)
    print('Wrote', HERE / 'figure1.pdf')


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else 'output/walkthrough/results.json')
