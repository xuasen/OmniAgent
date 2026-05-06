"""Gradient-free optimization algorithms."""

from __future__ import annotations

from typing import Callable


def nelder_mead(
    f: Callable[[list[float]], float],
    x0: list[float],
    max_iter: int = 200,
    tol: float = 1e-6,
    alpha: float = 1.0,
    gamma: float = 2.0,
    rho: float = 0.5,
    sigma: float = 0.5,
) -> tuple[list[float], float]:
    """
    Nelder-Mead simplex optimization. Returns (best_params, best_value).
    Minimizes f.
    """
    n = len(x0)
    if n == 0:
        return x0, f(x0)

    simplex = [x0[:]]
    for i in range(n):
        point = x0[:]
        point[i] += 0.05 * (abs(point[i]) + 1.0)
        simplex.append(point)

    values = [f(p) for p in simplex]

    for _ in range(max_iter):
        order = sorted(range(n + 1), key=lambda i: values[i])
        simplex = [simplex[i] for i in order]
        values = [values[i] for i in order]

        if max(abs(values[i] - values[0]) for i in range(1, n + 1)) < tol:
            break

        centroid = [sum(simplex[i][j] for i in range(n)) / n for j in range(n)]

        # Reflection
        worst = simplex[-1]
        reflected = [centroid[j] + alpha * (centroid[j] - worst[j]) for j in range(n)]
        fr = f(reflected)

        if values[0] <= fr < values[-2]:
            simplex[-1] = reflected
            values[-1] = fr
        elif fr < values[0]:
            expanded = [centroid[j] + gamma * (reflected[j] - centroid[j]) for j in range(n)]
            fe = f(expanded)
            if fe < fr:
                simplex[-1] = expanded
                values[-1] = fe
            else:
                simplex[-1] = reflected
                values[-1] = fr
        else:
            contracted = [centroid[j] + rho * (worst[j] - centroid[j]) for j in range(n)]
            fc = f(contracted)
            if fc < values[-1]:
                simplex[-1] = contracted
                values[-1] = fc
            else:
                for i in range(1, n + 1):
                    simplex[i] = [simplex[0][j] + sigma * (simplex[i][j] - simplex[0][j]) for j in range(n)]
                    values[i] = f(simplex[i])

    best_idx = min(range(n + 1), key=lambda i: values[i])
    return simplex[best_idx], values[best_idx]


def exponential_moving_average(values: list[float], alpha: float = 0.3) -> list[float]:
    """Compute EMA. Higher alpha = more weight to recent values."""
    if not values:
        return []
    ema = [values[0]]
    for v in values[1:]:
        ema.append(alpha * v + (1 - alpha) * ema[-1])
    return ema


def compute_deviation(actual: list[float], expected: list[float]) -> float | None:
    """Compute average relative deviation between actual and expected series."""
    if not actual or not expected or len(actual) != len(expected):
        return None
    deviations = []
    for a, e in zip(actual, expected):
        if e != 0:
            deviations.append(abs(a - e) / abs(e))
    if not deviations:
        return None
    return sum(deviations) / len(deviations)
