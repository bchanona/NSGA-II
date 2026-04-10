import numpy as np
import random
from src.domain.individual import random_individual
from src.domain.objectives import evaluate
from src.algorithm.pareto import fast_non_dominated_sort, crowding_distance
from src.algorithm.operators import tournament_select, crossover, mutate


def nsga2(knowledge, types, hours, days,
          n_posts, hours_available,
          pop_size=80, n_generations=100,
          crossover_prob=0.9, mutation_rate=0.3):

    print(f"\n[NSGA-II] Iniciando: {pop_size} individuos, {n_generations} generaciones")
    print(f"          Publicaciones/semana: {n_posts} | Horas disponibles: {hours_available}h\n")

    # ── Inicialización ────────────────────────────────────────────────────────
    population = [random_individual(n_posts, types, hours, days)
                  for _ in range(pop_size)]
    fitnesses  = [evaluate(ind, knowledge)
                  for ind in population]

    evolution = []

    for gen in range(n_generations):

        # ── Clasificar población actual en frentes ────────────────────────────
        fronts = fast_non_dominated_sort(fitnesses)

        # ── Crowding distance sobre la población actual ───────────────────────
        crowding = {}
        for front in fronts:
            crowding.update(crowding_distance(fitnesses, front))

        # ── Registro de evolución (frente F0) ────────────────────────────────
        f0_fits  = [fitnesses[i] for i in fronts[0]]
        avg_eng  = np.mean([-f[0] for f in f0_fits])
        avg_rch  = np.mean([-f[1] for f in f0_fits])
        avg_ret  = np.mean([-f[2] for f in f0_fits])
        avg_sat  = np.mean([ f[3] for f in f0_fits])
        avg_prod = np.mean([ f[4] for f in f0_fits])
        evolution.append((gen, avg_eng, avg_rch, avg_ret, avg_sat, avg_prod))

        if (gen + 1) % 10 == 0 or gen == 0:
            print(f"  Gen {gen+1:4d} | F0: {len(fronts[0]):3d} ind. | "
                  f"Eng: {avg_eng:.4f} | Reach: {avg_rch:.4f} | "
                  f"Ret: {avg_ret:.4f} | Sat: {avg_sat:.4f} | "
                  f"Prod: {avg_prod:.4f}")

        # ── Generación de descendencia ────────────────────────────────────────
        offspring      = []
        offspring_fits = []

        while len(offspring) < pop_size:
            i1 = tournament_select(population, fitnesses, fronts, crowding)
            i2 = tournament_select(population, fitnesses, fronts, crowding)

            if random.random() < crossover_prob:
                child = crossover(population[i1], population[i2],
                                  types, hours, days)
            else:
                import copy
                child = copy.deepcopy(population[i1])

            child = mutate(child, types, hours, days, mutation_rate)
            offspring.append(child)
            offspring_fits.append(evaluate(child, knowledge))

        # ── Población combinada (padres + hijos) ──────────────────────────────
        combined      = population + offspring
        combined_fits = fitnesses  + offspring_fits

        # ── Non-dominated sort sobre la combinada ─────────────────────────────
        new_fronts = fast_non_dominated_sort(combined_fits)

        # ── Crowding distance sobre la combinada ──────────────────────────────
        new_crowding = {}
        for front in new_fronts:
            new_crowding.update(crowding_distance(combined_fits, front))

        # ── Selección elitista: llenar la nueva población ─────────────────────
        #   Tomar frentes completos mientras quepan; el último frente parcial
        #   se ordena por crowding distance descendente.
        next_pop  = []
        next_fits = []

        for front in new_fronts:
            if len(next_pop) + len(front) <= pop_size:
                for i in front:
                    next_pop.append(combined[i])
                    next_fits.append(combined_fits[i])
            else:
                remaining = pop_size - len(next_pop)
                # Ordenar este frente por crowding distance (mayor = mejor)
                sorted_front = sorted(
                    front,
                    key=lambda i: new_crowding.get(i, 0.0),
                    reverse=True
                )
                for i in sorted_front[:remaining]:
                    next_pop.append(combined[i])
                    next_fits.append(combined_fits[i])
                break

        population = next_pop
        fitnesses  = next_fits

    # ── Resultado final ───────────────────────────────────────────────────────
    final_fronts   = fast_non_dominated_sort(fitnesses)
    pareto_indices = final_fronts[0]
    pareto_pop     = [population[i] for i in pareto_indices]
    pareto_fits    = [fitnesses[i]  for i in pareto_indices]

    print(f"\n[NSGA-II] Finalizado. Frente de Pareto: {len(pareto_pop)} soluciones.")
    return pareto_pop, pareto_fits, evolution


def run_nsga2(knowledge, types, hours, days,
              pop_size=60, generations=80, n_posts=7,
              mutation_rate=0.3, seed=42):
    

    from copy import deepcopy
    from src.domain.objectives import init_normalization

    random.seed(seed)
    init_normalization(knowledge, n_posts)

    # Población inicial aleatoria — se guarda para comparar vs optimizada
    initial_pop  = [random_individual(n_posts, types, hours, days)
                    for _ in range(pop_size)]
    initial_fits = [evaluate(ind, knowledge) for ind in initial_pop]

    pareto_pop, pareto_fits, evolution = nsga2(
        knowledge, types, hours, days,
        n_posts=n_posts,
        hours_available=10,
        pop_size=pop_size,
        n_generations=generations,
        mutation_rate=mutation_rate,
    )

    return pareto_pop, pareto_fits, evolution, initial_pop, initial_fits