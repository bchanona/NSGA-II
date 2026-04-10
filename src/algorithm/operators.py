import random
from copy import deepcopy
from src.utils.repair import repair
from src.domain.individual import THEMES


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
    El hijo hereda los genes completos (hour, day, type, theme) de cada padre
    según el punto de corte. Se repara antes de devolverlo.
    """
    if len(p1) < 2 or len(p2) < 2:
        return deepcopy(random.choice([p1, p2]))

    n     = min(len(p1), len(p2))
    point = random.randint(1, n - 1)

    child_raw = [deepcopy(pub) for pub in p1[:point]] + \
                [deepcopy(pub) for pub in p2[point:]]

    return repair(child_raw, types, hours, days)


def mutate(individual, types, hours, days, mutation_rate=0.3):
    """
    Mutación uniforme: con probabilidad mutation_rate cambia hora, día, tipo
    O tema (sᵢ) de cada publicación.
    Ahora hay 4 genes posibles por publicación (hour, day, type, theme).
    """
    mutant = deepcopy(individual)
    for pub in mutant:
        if random.random() < mutation_rate:
            choice = random.randint(0, 3)        # 0-3 en lugar de 0-2
            if choice == 0:
                pub['hour']  = random.choice(hours)
            elif choice == 1:
                pub['day']   = random.choice(days)
            elif choice == 2:
                pub['type']  = random.choice(types)
            else:
                pub['theme'] = random.choice(THEMES)   # ← mutación de sᵢ
    return repair(mutant, types, hours, days)