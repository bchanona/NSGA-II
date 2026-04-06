"""
operators.py — Operadores genéticos para NSGA-II (SocialGenOpt)

CORRECCIONES respecto a la versión anterior:
  1. tournament_select recibe el mapa rank precalculado en nsga2.py a través
     de 'fronts', construyéndolo una sola vez por generación en lugar de
     recalcularlo en cada llamada al selector (era O(pop²) innecesario).
  2. crossover llama a repair() para garantizar que el hijo cumpla la
     restricción MAX_PER_DAY antes de devolverlo.
  3. mutate conserva la llamada a repair() al final.
"""

import random
from copy import deepcopy
from src.utils.repair import repair


def _build_rank(fronts):
    """Construye dict {índice: rango} a partir de la lista de frentes."""
    rank = {}
    for r, front in enumerate(fronts):
        for i in front:
            rank[i] = r
    return rank


def tournament_select(population, fitnesses, fronts, crowding, k=2):
    """
    Selección por torneo binario NSGA-II:
      1. Comparar por rango (frente) — menor es mejor.
      2. En empate de rango, comparar por crowding distance — mayor es mejor.

    Parámetros
    ----------
    population : list
    fitnesses  : list[tuple]
    fronts     : list[list[int]]   — frentes actuales
    crowding   : dict[int, float]  — distancias de aglomeración
    k          : int               — tamaño del torneo (default 2)
    """
    rank = _build_rank(fronts)
    candidates = random.sample(range(len(population)), k)
    best = candidates[0]
    for c in candidates[1:]:
        if rank[c] < rank[best]:
            best = c
        elif rank[c] == rank[best] and crowding.get(c, 0.0) > crowding.get(best, 0.0):
            best = c
    return best


def crossover(p1, p2, types, hours, days):
    """
    Cruce de un punto entre dos padres.
    El punto de corte se elige sobre el mínimo de las longitudes para evitar
    índices fuera de rango.  El hijo se repara antes de devolverlo.
    """
    if len(p1) < 2 or len(p2) < 2:
        return deepcopy(random.choice([p1, p2]))

    n     = min(len(p1), len(p2))
    point = random.randint(1, n - 1)

    # Combinar segmentos (deepcopy de cada pub para no compartir referencias)
    child_raw = [deepcopy(pub) for pub in p1[:point]] + \
                [deepcopy(pub) for pub in p2[point:]]

    return repair(child_raw, types, hours, days)


def mutate(individual, types, hours, days, mutation_rate=0.3):
    """
    Mutación uniforme: con probabilidad mutation_rate cambia hora, día o tipo
    de cada publicación.  Aplica repair() al final.
    """
    mutant = deepcopy(individual)
    for pub in mutant:
        if random.random() < mutation_rate:
            choice = random.randint(0, 2)
            if choice == 0:
                pub['hour'] = random.choice(hours)
            elif choice == 1:
                pub['day']  = random.choice(days)
            else:
                pub['type'] = random.choice(types)
    return repair(mutant, types, hours, days)