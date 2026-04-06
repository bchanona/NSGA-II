
from collections import Counter
from src.utils.metrics_lookup import lookup_metrics
from src.domain.constants import PRODUCTION_COST

# Rangos globales — se inicializan con init_normalization()
_ENG_MAX  = 1.0
_RCH_MAX  = 1.0
_RET_MAX  = 1.0
_PROD_MAX = 35.0   # 7 pubs x short(5.0h) = caso más caro, fijo


def init_normalization(knowledge: dict, n_posts: int = 7):
    """
    Calcula los rangos máximos reales desde la knowledge base y los
    almacena en las variables globales de este módulo.

    Llama a esta función en main.py así:
        from src.domain.objectives import init_normalization
        knowledge, types, hours, days = load_knowledge(...)
        init_normalization(knowledge, args.max_posts)

    Parámetros
    ----------
    knowledge : dict  — el dict devuelto por load_knowledge()
    n_posts   : int   — número de publicaciones semanales (para escalar sumas)
    """
    global _ENG_MAX, _RCH_MAX, _RET_MAX

    eng_vals  = [v['engagement'] for v in knowledge.values()]
    rch_vals  = [v['reach']      for v in knowledge.values()]
    ret_vals  = [v['retention']  for v in knowledge.values()]

    # Suma máxima posible = n_posts × mejor valor individual
    _ENG_MAX = n_posts * max(eng_vals) if eng_vals else 1.0
    _RCH_MAX = n_posts * max(rch_vals) if rch_vals else 1.0
    _RET_MAX = max(ret_vals)            if ret_vals else 1.0   # es promedio, no suma

    # Evitar división por cero
    _ENG_MAX  = max(_ENG_MAX,  1e-9)
    _RCH_MAX  = max(_RCH_MAX,  1e-9)
    _RET_MAX  = max(_RET_MAX,  1e-9)

    print(f"[Objectives] Normalización inicializada:")
    print(f"  ENG_MAX  = {_ENG_MAX:.4f}  (n_posts={n_posts} x max_eng={max(eng_vals):.4f})")
    print(f"  RCH_MAX  = {_RCH_MAX:.4f}  (n_posts={n_posts} x max_rch={max(rch_vals):.4f})")
    print(f"  RET_MAX  = {_RET_MAX:.4f}  (max_ret promedio)")
    print(f"  PROD_MAX = {_PROD_MAX:.4f}  (fijo: n_posts x 5.0h)")


# ── Objetivo 1: Engagement normalizado ───────────────────────────────────────
def f1_engagement(individual, knowledge):
    if not individual:
        return 0.0
    engagements, _, _ = lookup_metrics(individual, knowledge)
    return -(sum(engagements) / _ENG_MAX)   # en [-1, 0]


# ── Objetivo 2: Alcance normalizado ──────────────────────────────────────────
def f2_reach(individual, knowledge):
    if not individual:
        return 0.0
    _, reaches, _ = lookup_metrics(individual, knowledge)
    return -(sum(reaches) / _RCH_MAX)       # en [-1, 0]


# ── Objetivo 3: Retención normalizada ────────────────────────────────────────
def f3_retention(individual, knowledge):
    if not individual:
        return 0.0
    _, _, retentions = lookup_metrics(individual, knowledge)
    avg = sum(retentions) / len(retentions)
    return -(avg / _RET_MAX)                # en [-1, 0]


# ── Objetivo 4: Saturación de audiencia + homogeneidad de formato ─────────────
def f4_saturation(individual, knowledge=None):
    """
    Combina dos señales en [0, 1]:
      a) time_sat  — pubs en el mismo día con <3h de diferencia.
      b) type_sat  — si >60% de pubs son del mismo tipo (saturación de formato).
    Ponderación 50/50.
    """
    if not individual:
        return 1.0

    n = len(individual)

    by_day = {}
    for pub in individual:
        by_day.setdefault(pub['day'], []).append(pub['hour'])

    conflicts = 0
    for hrs in by_day.values():
        s = sorted(hrs)
        for a, b in zip(s, s[1:]):
            if b - a < 3:
                conflicts += 1
    time_sat = conflicts / max(n - 1, 1)

    type_counts = Counter(p['type'] for p in individual)
    top_ratio   = type_counts.most_common(1)[0][1] / n
    type_sat    = max(0.0, (top_ratio - 0.60) / 0.40)

    return 0.5 * time_sat + 0.5 * type_sat


# ── Objetivo 5: Tiempo de producción normalizado ──────────────────────────────
def f5_production_time(individual, knowledge=None, hours_available=10):
    if not individual:
        return 1.0
    prod_time    = sum(PRODUCTION_COST.get(p['type'], 2.0) for p in individual)
    time_penalty = max(0, prod_time - hours_available)
    return (prod_time + time_penalty) / _PROD_MAX   # en [0, ~1]


# ── Vector de objetivos ───────────────────────────────────────────────────────
OBJECTIVES = [f1_engagement, f2_reach, f3_retention, f4_saturation, f5_production_time]


def evaluate(individual, knowledge):
    if not individual:
        return (0.0, 0.0, 0.0, 1.0, 1.0)
    return tuple(f(individual, knowledge) for f in OBJECTIVES)