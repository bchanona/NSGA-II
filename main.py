import argparse
import random
import numpy as np
import os
from dotenv import load_dotenv

from src.knowledge.loader import load_knowledge
from src.algorithm.nsga2 import nsga2
from src.output.exporter import export_results, print_best_calendars
from src.domain.objectives import init_normalization   

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def main():
    load_dotenv()

    default_knowledge = os.getenv("KNOWLEDGE_FILE", os.path.join(BASE_DIR, "data", "knowledge_base.csv"))
    default_platform        = os.getenv("PLATFORM",         None)
    default_max_posts       = int(os.getenv("MAX_POSTS",    7))
    default_hours_available = int(os.getenv("HOURS_AVAILABLE", 10))
    default_population      = int(os.getenv("POPULATION_SIZE", 80))
    default_generations     = int(os.getenv("GENERATIONS",  100))
    default_crossover_prob  = float(os.getenv("CROSSOVER_PROB", 0.9))
    default_mutation_rate   = float(os.getenv("MUTATION_RATE",  0.3))
    default_output          = os.getenv("OUTPUT_DIR",       "./output_nsga2")
    default_seed            = int(os.getenv("SEED",         42))

    parser = argparse.ArgumentParser(description="SocialGenOpt — NSGA-II para redes sociales")
    parser.add_argument("--knowledge",        default=default_knowledge)
    parser.add_argument("--platform",         default=default_platform)
    parser.add_argument("--max_posts",        type=int,   default=default_max_posts)
    parser.add_argument("--hours_available",  type=int,   default=default_hours_available)
    parser.add_argument("--population",       type=int,   default=default_population)
    parser.add_argument("--generations",      type=int,   default=default_generations)
    parser.add_argument("--crossover_prob",   type=float, default=default_crossover_prob)
    parser.add_argument("--mutation_rate",    type=float, default=default_mutation_rate)
    parser.add_argument("--output",           default=default_output)
    parser.add_argument("--seed",             type=int,   default=default_seed)
    args = parser.parse_args()

    random.seed(args.seed)
    np.random.seed(args.seed)

    knowledge, types, hours, days = load_knowledge(args.knowledge, args.platform)

    # Inicializar rangos de normalización DESDE la KB real
    # Esto garantiza que f1/f2/f3 queden en [-1, 0] sin importar el dataset
    init_normalization(knowledge, n_posts=args.max_posts)

    pareto_pop, pareto_fits, evolution = nsga2(
        knowledge, types, hours, days,
        args.max_posts,
        args.hours_available,
        args.population,
        args.generations,
        args.crossover_prob,
        args.mutation_rate,
    )

    pareto_df, evo_df, best_df = export_results(
        pareto_pop, pareto_fits, evolution, args.output
    )

    print_best_calendars(best_df)
    print(f"\n[OK] Resultados guardados en: {args.output}/")

if __name__ == "__main__":
    main()