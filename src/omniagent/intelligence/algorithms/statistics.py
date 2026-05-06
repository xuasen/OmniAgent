"""Statistical tests for experiment evaluation."""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass
class StatResult:
    statistic: float
    p_value: float
    significant: bool
    confidence_level: float


def chi_squared_test(
    successes_a: int, total_a: int,
    successes_b: int, total_b: int,
    alpha: float = 0.05,
) -> StatResult:
    """Chi-squared test for success rate comparison between two variants."""
    if total_a == 0 or total_b == 0:
        return StatResult(statistic=0, p_value=1.0, significant=False, confidence_level=1 - alpha)

    failures_a = total_a - successes_a
    failures_b = total_b - successes_b
    total = total_a + total_b
    total_success = successes_a + successes_b
    total_failure = failures_a + failures_b

    e_sa = total_a * total_success / total
    e_fa = total_a * total_failure / total
    e_sb = total_b * total_success / total
    e_fb = total_b * total_failure / total

    chi2 = 0.0
    for observed, expected in [
        (successes_a, e_sa), (failures_a, e_fa),
        (successes_b, e_sb), (failures_b, e_fb),
    ]:
        if expected > 0:
            chi2 += (observed - expected) ** 2 / expected

    p_value = 1.0 - _chi2_cdf(chi2, df=1)
    return StatResult(statistic=chi2, p_value=p_value, significant=p_value < alpha, confidence_level=1 - alpha)


def welch_t_test(
    mean_a: float, std_a: float, n_a: int,
    mean_b: float, std_b: float, n_b: int,
    alpha: float = 0.05,
) -> StatResult:
    """Welch's t-test for continuous metric comparison."""
    if n_a < 2 or n_b < 2:
        return StatResult(statistic=0, p_value=1.0, significant=False, confidence_level=1 - alpha)

    se_sq = std_a**2 / n_a + std_b**2 / n_b
    if se_sq == 0:
        return StatResult(statistic=0, p_value=1.0, significant=False, confidence_level=1 - alpha)

    se = math.sqrt(se_sq)
    t_stat = (mean_a - mean_b) / se

    num = se_sq**2
    denom = (std_a**2 / n_a) ** 2 / (n_a - 1) + (std_b**2 / n_b) ** 2 / (n_b - 1)
    df = num / denom if denom > 0 else 1

    p_value = 2.0 * (1.0 - _t_cdf(abs(t_stat), df))
    return StatResult(statistic=t_stat, p_value=p_value, significant=p_value < alpha, confidence_level=1 - alpha)


def sequential_test(
    successes: int, failures: int,
    p0: float = 0.5, p1: float = 0.6,
    alpha: float = 0.05, beta: float = 0.2,
) -> str:
    """
    Sequential Probability Ratio Test (SPRT).
    Returns: "continue", "accept_h1", or "reject_h1"
    """
    if p0 <= 0 or p0 >= 1 or p1 <= 0 or p1 >= 1 or p0 == p1:
        return "continue"
    if successes + failures == 0:
        return "continue"

    log_A = math.log((1 - beta) / alpha)
    log_B = math.log(beta / (1 - alpha))

    llr = successes * math.log(p1 / p0) + failures * math.log((1 - p1) / (1 - p0))

    if llr >= log_A:
        return "accept_h1"
    elif llr <= log_B:
        return "reject_h1"
    return "continue"


def _chi2_cdf(x: float, df: int) -> float:
    """Approximate chi-squared CDF using regularized incomplete gamma function."""
    if x <= 0:
        return 0.0
    return _regularized_gamma(df / 2.0, x / 2.0)


def _t_cdf(x: float, df: float) -> float:
    """Approximate Student's t CDF using regularized incomplete beta function."""
    if df <= 0:
        return 0.5
    t2 = x * x
    return 1.0 - 0.5 * _regularized_beta(df / (df + t2), df / 2.0, 0.5)


def _regularized_gamma(a: float, x: float, max_iter: int = 200) -> float:
    """Lower regularized incomplete gamma function P(a, x)."""
    if x < 0:
        return 0.0
    if x == 0:
        return 0.0

    if x < a + 1:
        # Series expansion
        term = 1.0 / a
        total = term
        for n in range(1, max_iter):
            term *= x / (a + n)
            total += term
            if abs(term) < 1e-10:
                break
        return total * math.exp(-x + a * math.log(x) - math.lgamma(a))
    else:
        # Continued fraction
        return 1.0 - _upper_gamma_cf(a, x)


def _upper_gamma_cf(a: float, x: float, max_iter: int = 200) -> float:
    """Upper incomplete gamma via continued fraction (Lentz's method)."""
    f = x - a + 1
    if abs(f) < 1e-30:
        f = 1e-30
    c = f
    d = 0.0
    result = 0.0

    for n in range(1, max_iter):
        an = n * (a - n)
        bn = x - a + 2 * n + 1
        d = bn + an * d
        if abs(d) < 1e-30:
            d = 1e-30
        d = 1.0 / d
        c = bn + an / c
        if abs(c) < 1e-30:
            c = 1e-30
        delta = c * d
        f *= delta
        if abs(delta - 1.0) < 1e-10:
            break

    return math.exp(-x + a * math.log(x) - math.lgamma(a)) / f


def _regularized_beta(x: float, a: float, b: float, max_iter: int = 200) -> float:
    """Regularized incomplete beta function I_x(a, b) using continued fraction."""
    if x <= 0:
        return 0.0
    if x >= 1:
        return 1.0

    log_prefix = math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b) + a * math.log(x) + b * math.log(1 - x)
    prefix = math.exp(log_prefix)

    # Lentz's continued fraction
    f = 1.0
    c = 1.0
    d = 1.0 - (a + b) * x / (a + 1)
    if abs(d) < 1e-30:
        d = 1e-30
    d = 1.0 / d
    f = d

    for m in range(1, max_iter):
        # Even step
        numerator = m * (b - m) * x / ((a + 2 * m - 1) * (a + 2 * m))
        d = 1.0 + numerator * d
        if abs(d) < 1e-30:
            d = 1e-30
        d = 1.0 / d
        c = 1.0 + numerator / c
        if abs(c) < 1e-30:
            c = 1e-30
        f *= c * d

        # Odd step
        numerator = -(a + m) * (a + b + m) * x / ((a + 2 * m) * (a + 2 * m + 1))
        d = 1.0 + numerator * d
        if abs(d) < 1e-30:
            d = 1e-30
        d = 1.0 / d
        c = 1.0 + numerator / c
        if abs(c) < 1e-30:
            c = 1e-30
        delta = c * d
        f *= delta

        if abs(delta - 1.0) < 1e-10:
            break

    return prefix * f / a
