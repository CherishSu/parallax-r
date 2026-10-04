"""Exploratory paired statistics; scenario is the independent resampling unit."""
import itertools
import math
import random
from collections import defaultdict


def quantile(values, q):
    ordered = sorted(values)
    position = (len(ordered) - 1) * q
    low = int(position)
    high = min(low + 1, len(ordered) - 1)
    return ordered[low] + (ordered[high] - ordered[low]) * (position - low)


def paired_statistics(records, draws=10000, seed=20261004):
    """Records contain scenario_id and delta; all repeats are already averaged.

    Estimate a case-weighted mean. Resample entire scenarios with replacement.
    Sign-flip all differences within a scenario together under a symmetric-null
    assumption. This is not proof of causation or a randomization design.
    """
    if type(draws) is not int or draws < 100:
        raise ValueError('draws must be an integer of at least 100')
    clusters = defaultdict(list)
    for row in records:
        sid, value = row['scenario_id'], row['delta']
        if not isinstance(sid, str) or not sid:
            raise ValueError('scenario_id must be nonempty')
        if type(value) not in (int, float) or not math.isfinite(value):
            raise ValueError('delta must be finite')
        clusters[sid].append(value)
    groups = [clusters[k] for k in sorted(clusters)]
    n = sum(map(len, groups))
    observed = sum(map(sum, groups)) / n if n else None
    result = dict(cases=n, scenarios=len(groups), mean_delta=observed,
                  seed=seed, bootstrap_draws=draws, confidence_level=.95,
                  weighting='case-weighted', unit='scenario_id',
                  alternative='two-sided', bootstrap_ci=None, sign_flip_p=None)
    if len(groups) < 2:
        return dict(result, status='UNDEFINED_FEWER_THAN_TWO_SCENARIOS')
    rng = random.Random(seed)
    sampled = []
    for _ in range(draws):
        sample = rng.choices(groups, k=len(groups))
        sampled.append(sum(map(sum, sample)) / sum(map(len, sample)))
    result['bootstrap_ci'] = [quantile(sampled, .025), quantile(sampled, .975)]
    totals = [sum(g) for g in groups]
    threshold = abs(observed)
    exact = len(groups) <= 16
    signs = (itertools.product((-1, 1), repeat=len(groups)) if exact else
             (tuple(rng.choice((-1, 1)) for _ in groups) for _ in range(draws)))
    extreme = total = 0
    for signs_i in signs:
        statistic = abs(sum(s * v for s, v in zip(signs_i, totals)) / n)
        extreme += statistic >= threshold - 1e-12
        total += 1
    result.update(status='DEFINED', sign_flip_method='exact' if exact else 'monte_carlo',
                  sign_flip_draws=total,
                  sign_flip_p=extreme / total if exact else (extreme + 1) / (total + 1))
    return result


def analyze_run(run, draws=10000, seed=20261004):
    outputs = {}
    for label in ('harmful', 'benign'):
        records = [dict(scenario_id=r['case']['scenario_id'], delta=r['metrics']['delta'])
                   for r in run['results'] if not r['case'].get('condition')
                   and r['case']['ground_truth'] == label and r['metrics']['eligible']]
        outputs[label] = paired_statistics(records, draws, seed)
    return dict(mode=run['mode'], interpretation=('SCRIPTED_DEMO_NOT_RESEARCH' if run['mode']=='demo'
                else 'EXPLORATORY_COMPLETE_CASE_ANALYSIS'), by_class=outputs,
                limitations=['Small selected synthetic sample; no population-representativeness claim.',
                             'Sign-flip test assumes independent scenarios and joint sign symmetry under the null.',
                             'Complete-case selection may bias results; report exclusions and abstentions.',
                             'Bootstrap intervals may degenerate when all observed differences are equal.',
                             'Statistics do not change the approved continuation rules.'])
