"""
exporter.py — Exportación de resultados para SocialGenOpt

CORRECCIONES respecto a la versión anterior:
  1. evolution.csv ahora incluye las columnas avg_saturation y avg_prod_time
     que nsga2.py registra en cada generación (antes se perdían).
  2. score_solution: se eliminó el 'diversity_bonus' artificial que era
     consistente con la penalización removida en objectives.py.
     Ahora el ranking usa engagement como criterio principal, con retención
     y alcance como desempate secundario.
  3. print_best_calendars: sin cambios de lógica.
"""

import pandas as pd
import os
from src.domain.constants import DAY_NAMES


def export_results(pareto_pop, pareto_fits, evolution, output_dir, n_best=3):
    os.makedirs(output_dir, exist_ok=True)

    # ── Frente de Pareto completo ─────────────────────────────────────────────
    rows = []
    for idx, (ind, fit) in enumerate(zip(pareto_pop, pareto_fits)):
        for pub in ind:
            rows.append({
                'solution_id': idx,
                'day':         pub['day'],
                'day_name':    DAY_NAMES[pub['day']],
                'hour':        pub['hour'],
                'type':        pub['type'],
                'engagement':  round(-fit[0], 6),
                'reach':       round(-fit[1], 6),
                'retention':   round(-fit[2], 6),
                'saturation':  round( fit[3], 6),
                'prod_time':   round( fit[4], 6),
            })
    pareto_df = pd.DataFrame(rows)
    pareto_df.to_csv(os.path.join(output_dir, 'pareto_front.csv'), index=False)

    # ── Evolución por generación ──────────────────────────────────────────────
    evo_cols = ['generation', 'avg_engagement', 'avg_reach',
                'avg_retention', 'avg_saturation', 'avg_prod_time']
    evo_df = pd.DataFrame(evolution, columns=evo_cols)
    evo_df.to_csv(os.path.join(output_dir, 'evolution.csv'), index=False)

    # ── Top-N mejores soluciones ──────────────────────────────────────────────
    def score_solution(item):
        """
        Ranking limpio:
          - Prioridad 1: mayor engagement (fit[0] es negativo → menor = mejor).
          - Prioridad 2: menor saturación.
          - Prioridad 3: menor tiempo de producción.
        """
        _, fit = item
        return (fit[0], fit[3], fit[4])   # todo a minimizar, consistente

    ranked = sorted(zip(pareto_pop, pareto_fits), key=score_solution)

    best_rows = []
    for rank, (ind, fit) in enumerate(ranked[:n_best]):
        for pub in sorted(ind, key=lambda p: (p['day'], p['hour'])):
            best_rows.append({
                'rank':       rank + 1,
                'day_name':   DAY_NAMES[pub['day']],
                'hour':       f"{pub['hour']:02d}:00",
                'type':       pub['type'],
                'engagement': round(-fit[0], 4),
                'reach':      round(-fit[1], 4),
                'retention':  round(-fit[2], 4),
                'saturation': round( fit[3], 4),
                'prod_hours': round( fit[4], 4),
            })
    best_df = pd.DataFrame(best_rows)
    best_df.to_csv(os.path.join(output_dir, 'best_calendars.csv'), index=False)

    return pareto_df, evo_df, best_df


def print_best_calendars(best_df):
    print("\n" + "═" * 60)
    print("  TOP 3 CALENDARIOS ÓPTIMOS")
    print("═" * 60)
    for rank in best_df['rank'].unique():
        sub = best_df[best_df['rank'] == rank]
        row = sub.iloc[0]
        print(f"\n  Solución #{rank}")
        print(f"  Engagement: {row['engagement']:.4f} | "
              f"Reach: {row['reach']:.4f} | "
              f"Retención: {row['retention']:.4f}")
        print(f"  Saturación: {row['saturation']:.4f} | "
              f"Tiempo producción: {row['prod_hours']:.2f}h")
        print(f"  {'Día':<12} {'Hora':<8} {'Tipo'}")
        print(f"  {'-'*35}")
        for _, pub in sub.iterrows():
            print(f"  {pub['day_name']:<12} {pub['hour']:<8} {pub['type']}")
    print("═" * 60)