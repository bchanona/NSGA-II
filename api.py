"""
api.py — FastAPI backend para SocialGenOpt
SaaS de optimización de calendarios editoriales
para creadores de contenido y agencias de marketing digital.

RUTAS:
  POST /api/optimize          → Ejecuta NSGA-II, devuelve resultado completo
  GET  /api/evolution         → Gráfica de evolución de aptitud por generación
  GET  /api/pareto            → Frontera de Pareto (scatter 3D)
  GET  /api/top-solutions     → Tabla comparativa top-3 individuos
  GET  /api/calendar/{rank}   → Calendario semanal visual del individuo rank
  GET  /api/comparison        → Estrategia inicial aleatoria vs optimizada
  GET  /                      → Frontend (index.html)
"""

import os, sys, json, time
from pathlib import Path
from typing import Optional
from copy import deepcopy

sys.path.insert(0, str(Path(__file__).parent))

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from src.knowledge.loader import load_knowledge
from src.domain.objectives import evaluate
from src.algorithm.nsga2 import run_nsga2
from src.domain.constants import DAY_NAMES, PRODUCTION_COST, THEME_LABELS

# ── App ────────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="SocialGenOpt API",
    description="Optimización multiobjetivo de calendarios editoriales para redes sociales",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

STATIC_DIR = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

_cache: dict = {}

DATA_PATH = Path(__file__).parent / "data" / "knowledge_base.csv"


# ── Modelos Pydantic ────────────────────────────────────────────────────────────
class OptimizeRequest(BaseModel):
    platform:        Optional[str]   = "instagram"
    pop_size:        Optional[int]   = 60
    generations:     Optional[int]   = 80
    n_posts:         Optional[int]   = 7
    mutation_rate:   Optional[float] = 0.3
    hours_available: Optional[int]   = 10


# ── Helpers ─────────────────────────────────────────────────────────────────────
def _score(fit):
    """Ranking: mayor eng, menor saturación, menor prod_time."""
    return (fit[0], fit[3], fit[4])


def _get_top(n=3):
    if "pareto_pop" not in _cache:
        raise HTTPException(status_code=400, detail="Primero ejecuta /api/optimize")
    pairs = list(zip(_cache["pareto_pop"], _cache["pareto_fits"]))
    ranked = sorted(pairs, key=lambda x: _score(x[1]))
    return ranked[:n]


def _pub_dict(pub, fit):
    """Serializa una publicación incluyendo el campo theme (sᵢ)."""
    return {
        "day":        pub['day'],
        "day_name":   DAY_NAMES[pub['day']],
        "hour":       pub['hour'],
        "hour_fmt":   f"{pub['hour']:02d}:00",
        "type":       pub['type'],
        "theme":      pub.get('theme', 'educativo'),
        "theme_label":THEME_LABELS.get(pub.get('theme', 'educativo'), pub.get('theme', '')),
        "prod_cost":  PRODUCTION_COST.get(pub['type'], 2.0),
    }


# ── Rutas ───────────────────────────────────────────────────────────────────────

@app.get("/")
def root():
    return FileResponse(str(STATIC_DIR / "index.html"))


@app.post("/api/optimize")
def optimize(req: OptimizeRequest):
    """Ejecuta el algoritmo NSGA-II completo."""
    knowledge, types, hours, days = load_knowledge(str(DATA_PATH), req.platform)

    import time as time_module
    seed = int(time_module.time() * 1000) % 2147483647

    t0 = time.time()
    pareto_pop, pareto_fits, evolution, initial_pop, initial_fits = run_nsga2(
        knowledge, types, hours, days,
        pop_size=req.pop_size,
        generations=req.generations,
        n_posts=req.n_posts,
        mutation_rate=req.mutation_rate,
        hours_available=req.hours_available,
        seed=seed,
    )
    elapsed = round(time.time() - t0, 2)

    _cache.update({
        "pareto_pop":   pareto_pop,
        "pareto_fits":  pareto_fits,
        "evolution":    evolution,
        "initial_pop":  initial_pop,
        "initial_fits": initial_fits,
        "knowledge":    knowledge,
        "types": types, "hours": hours, "days": days,
        "params": req.dict(),
    })

    return {
        "status":      "ok",
        "elapsed_sec": elapsed,
        "pareto_size": len(pareto_pop),
        "generations": req.generations,
        "message":     f"Optimización completada en {elapsed}s. {len(pareto_pop)} soluciones en el frente de Pareto."
    }


@app.get("/api/evolution")
def get_evolution():
    if "evolution" not in _cache:
        raise HTTPException(status_code=400, detail="Primero ejecuta /api/optimize")
    evo = _cache["evolution"]
    return {
        "labels": [e[0] for e in evo],
        "series": {
            "engagement": [round(e[1], 4) for e in evo],
            "reach":      [round(e[2], 4) for e in evo],
            "retention":  [round(e[3], 4) for e in evo],
            "saturation": [round(e[4], 4) for e in evo],
            "prod_time":  [round(e[5], 4) for e in evo],
        }
    }


@app.get("/api/pareto")
def get_pareto():
    if "pareto_fits" not in _cache:
        raise HTTPException(status_code=400, detail="Primero ejecuta /api/optimize")
    points = []
    for i, fit in enumerate(_cache["pareto_fits"]):
        points.append({
            "id":         i,
            "engagement": round(-fit[0], 4),
            "reach":      round(-fit[1], 4),
            "retention":  round(-fit[2], 4),
            "saturation": round( fit[3], 4),
            "prod_time":  round( fit[4], 4),
        })
    return {"points": points, "total": len(points)}


@app.get("/api/top-solutions")
def get_top_solutions(n: int = Query(default=3, ge=1, le=10)):
    """
    Tabla comparativa de las N mejores soluciones.
    Incluye el campo theme (sᵢ) en cada publicación.
    """
    top = _get_top(n)
    solutions = []
    for rank, (ind, fit) in enumerate(top):
        pubs = sorted(ind, key=lambda p: (p['day'], p['hour']))

        # Calcular coherencia temática de la secuencia para mostrarlo en UI
        themes_seq = [p.get('theme', 'educativo') for p in pubs]
        theme_coherence = _theme_coherence_score(themes_seq)

        solutions.append({
            "rank":    rank + 1,
            "metrics": {
                "engagement":      round(-fit[0], 4),
                "reach":           round(-fit[1], 4),
                "retention":       round(-fit[2], 4),
                "saturation":      round( fit[3], 4),
                "prod_hours":      round( fit[4] * 35, 2),
                "theme_coherence": round(theme_coherence, 4),   # ← sᵢ info
            },
            "theme_sequence": themes_seq,   # secuencia cronológica de temas
            "posts": [_pub_dict(p, fit) for p in pubs],
        })
    return {"solutions": solutions}


@app.get("/api/calendar/{rank}")
def get_calendar(rank: int):
    """
    Calendario semanal del individuo en posición `rank`.
    Cada publicación incluye el campo theme (sᵢ).
    """
    top = _get_top(rank)
    if rank < 1 or rank > len(top):
        raise HTTPException(status_code=404, detail=f"rank debe ser entre 1 y {len(top)}")

    ind, fit = top[rank - 1]

    grid = {d: [] for d in range(7)}
    for pub in ind:
        grid[pub['day']].append({
            "hour":        pub['hour'],
            "hour_fmt":    f"{pub['hour']:02d}:00",
            "type":        pub['type'],
            "theme":       pub.get('theme', 'educativo'),
            "theme_label": THEME_LABELS.get(pub.get('theme', 'educativo'), ''),
            "prod_cost":   PRODUCTION_COST.get(pub['type'], 2.0),
        })

    for d in grid:
        grid[d] = sorted(grid[d], key=lambda x: x['hour'])

    days_list = [
        {"day": d, "name": DAY_NAMES[d], "posts": grid[d]}
        for d in range(7)
    ]

    # Secuencia cronológica completa para mostrar en UI
    all_pubs_sorted = sorted(ind, key=lambda p: (p['day'], p['hour']))
    themes_seq = [p.get('theme', 'educativo') for p in all_pubs_sorted]

    return {
        "rank":    rank,
        "metrics": {
            "engagement":      round(-fit[0], 4),
            "reach":           round(-fit[1], 4),
            "retention":       round(-fit[2], 4),
            "saturation":      round( fit[3], 4),
            "theme_coherence": round(_theme_coherence_score(themes_seq), 4),
        },
        "theme_sequence": themes_seq,
        "calendar": days_list,
    }


@app.get("/api/comparison")
def get_comparison():
    if "initial_fits" not in _cache or "pareto_fits" not in _cache:
        raise HTTPException(status_code=400, detail="Primero ejecuta /api/optimize")

    init_fits  = _cache["initial_fits"]
    final_fits = _cache["pareto_fits"]

    def avg_metrics(fits):
        n = len(fits)
        return {
            "engagement": round(-sum(f[0] for f in fits)/n, 4),
            "reach":      round(-sum(f[1] for f in fits)/n, 4),
            "retention":  round(-sum(f[2] for f in fits)/n, 4),
            "saturation": round( sum(f[3] for f in fits)/n, 4),
            "prod_time":  round( sum(f[4] for f in fits)/n, 4),
        }

    initial_avg   = avg_metrics(init_fits)
    optimized_avg = avg_metrics(final_fits)

    # Coherencia temática promedio de cada población
    def avg_theme_coherence(pop):
        scores = []
        for ind in pop:
            sorted_pubs = sorted(ind, key=lambda p: (p['day'], p['hour']))
            themes_seq  = [p.get('theme', 'educativo') for p in sorted_pubs]
            scores.append(_theme_coherence_score(themes_seq))
        return round(sum(scores) / len(scores), 4) if scores else 0.0

    initial_avg["theme_coherence"]   = avg_theme_coherence(_cache["initial_pop"])
    optimized_avg["theme_coherence"] = avg_theme_coherence(_cache["pareto_pop"])

    deltas = {}
    for k in initial_avg:
        i_val = initial_avg[k]
        o_val = optimized_avg[k]
        if i_val != 0:
            deltas[k] = round((o_val - i_val) / abs(i_val) * 100, 1)
        else:
            deltas[k] = 0.0

    return {
        "initial":        initial_avg,
        "optimized":      optimized_avg,
        "deltas":         deltas,
        "initial_size":   len(init_fits),
        "optimized_size": len(final_fits),
    }


@app.get("/api/status")
def status():
    return {
        "ready":  "pareto_pop" in _cache,
        "params": _cache.get("params"),
    }


# ── Utilidad interna ─────────────────────────────────────────────────────────
def _theme_coherence_score(themes_seq: list) -> float:
    """
    Calcula la coherencia promedio de la secuencia temática (sᵢ).
    Retorna un valor en [0, 1] donde 1 = máxima coherencia.
    """
    from src.domain.individual import THEME_AFFINITY
    if len(themes_seq) < 2:
        return 1.0
    scores = []
    for prev, curr in zip(themes_seq, themes_seq[1:]):
        scores.append(THEME_AFFINITY.get(prev, {}).get(curr, 0.6))
    return sum(scores) / len(scores)