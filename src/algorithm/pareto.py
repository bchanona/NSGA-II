"""
pareto.py — Non-dominated sorting y crowding distance para NSGA-II
Alineado con el algoritmo del artículo GfG / Deb et al. 2002.

CORRECCIONES respecto a la versión anterior:
  1. fast_non_dominated_sort: construye S[p] y n_dom[p] en una sola pasada
     (igual que el paper original), evitando el doble conteo que causaba
     clasificaciones incorrectas de frentes.
  2. crowding_distance: omite la acumulación cuando el individuo ya tiene inf,
     y usa el rango del frente local (no global) para la normalización.
"""


def dominates(a, b):
    """
    True si 'a' domina a 'b' bajo minimización:
      - igual o mejor en TODOS los objetivos, Y
      - estrictamente mejor en AL MENOS uno.
    """
    at_least_as_good = all(ai <= bi for ai, bi in zip(a, b))
    strictly_better  = any(ai <  bi for ai, bi in zip(a, b))
    return at_least_as_good and strictly_better


def fast_non_dominated_sort(fitnesses):
    """
    Clasifica toda la población en frentes de Pareto F1, F2, …

    Retorna list[list[int]]: cada sub-lista contiene índices de individuos.
    """
    n = len(fitnesses)
    S     = [[] for _ in range(n)]   # S[p]: índices que p domina
    n_dom = [0] * n                  # n_dom[p]: cuántos dominan a p
    fronts = [[]]

    for p in range(n):
        for q in range(n):
            if p == q:
                continue
            if dominates(fitnesses[p], fitnesses[q]):
                S[p].append(q)
            elif dominates(fitnesses[q], fitnesses[p]):
                n_dom[p] += 1

        if n_dom[p] == 0:
            fronts[0].append(p)

    i = 0
    while fronts[i]:
        next_front = []
        for p in fronts[i]:
            for q in S[p]:
                n_dom[q] -= 1
                if n_dom[q] == 0:
                    next_front.append(q)
        i += 1
        fronts.append(next_front)

    return [f for f in fronts if f]


def crowding_distance(fitnesses, front):
    """
    Distancia de aglomeración para cada individuo de un frente.

    Parámetros
    ----------
    fitnesses : list[tuple]   — fitness de TODA la población
    front     : list[int]     — índices de los individuos en el frente

    Retorna dict[int, float]
    """
    l = len(front)
    if l <= 2:
        return {i: float('inf') for i in front}

    n_obj = len(fitnesses[0])
    dist  = {i: 0.0 for i in front}

    for obj in range(n_obj):
        sorted_front = sorted(front, key=lambda i: fitnesses[i][obj])

        dist[sorted_front[0]]  = float('inf')
        dist[sorted_front[-1]] = float('inf')

        f_min = fitnesses[sorted_front[0]][obj]
        f_max = fitnesses[sorted_front[-1]][obj]
        span  = f_max - f_min if f_max != f_min else 1e-9

        for k in range(1, l - 1):
            if dist[sorted_front[k]] == float('inf'):
                continue
            dist[sorted_front[k]] += (
                fitnesses[sorted_front[k + 1]][obj] -
                fitnesses[sorted_front[k - 1]][obj]
            ) / span

    return dist