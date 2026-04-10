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
    """
    global _ENG_MAX, _RCH_MAX, _RET_MAX

    eng_vals  = [v['engagement'] for v in knowledge.values()]
    rch_vals  = [v['reach']      for v in knowledge.values()]
    ret_vals  = [v['retention']  for v in knowledge.values()]

    _ENG_MAX = n_posts * max(eng_vals) if eng_vals else 1.0
    _RCH_MAX = n_posts * max(rch_vals) if rch_vals else 1.0
    _RET_MAX = max(ret_vals)            if ret_vals else 1.0

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


# ── Objetivo 4: Saturación de audiencia + homogeneidad de formato
#               + penalización por secuencia temática incoherente (sᵢ) ────────
def f4_saturation(individual, knowledge=None):
    """
    Combina tres señales en [0, 1]:

      a) time_sat   — publicaciones en el mismo día con < 3h de diferencia
                      (saturación temporal).
      b) type_sat   — si > 60% de publicaciones son del mismo tipo
                      (saturación de formato).
      c) theme_sat  — penalización por baja coherencia de secuencia temática (sᵢ):
                      se evalúa la afinidad entre temas consecutivos según el
                      orden cronológico del calendario; una secuencia con temas
                      repetidos o con baja afinidad eleva la saturación percibida.

    Ponderación: 40% time_sat + 30% type_sat + 30% theme_sat.

    La incorporación de theme_sat materializa la variable de decisión sᵢ
    (secuencia temática) dentro de la función de saturación existente,
    sin añadir un sexto objetivo al algoritmo.
    """
    if not individual:
        return 1.0

    from src.domain.individual import THEME_AFFINITY, THEMES

    n = len(individual)

    # ── a) Saturación temporal ────────────────────────────────────────
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

    # ── b) Saturación de formato ──────────────────────────────────────
    type_counts = Counter(p['type'] for p in individual)
    top_ratio   = type_counts.most_common(1)[0][1] / n
    type_sat    = max(0.0, (top_ratio - 0.60) / 0.40)

    # ── c) Saturación de secuencia temática (sᵢ) ─────────────────────
    # Ordenar publicaciones cronológicamente (día, hora) para evaluar la
    # secuencia tal como la experimenta la audiencia.
    sorted_pubs = sorted(individual, key=lambda p: (p['day'], p['hour']))
    themes_seq  = [p.get('theme', 'educativo') for p in sorted_pubs]

    if len(themes_seq) >= 2:
        affinity_scores = []
        for prev, curr in zip(themes_seq, themes_seq[1:]):
            score = THEME_AFFINITY.get(prev, {}).get(curr, 0.6)
            affinity_scores.append(score)
        avg_affinity = sum(affinity_scores) / len(affinity_scores)
        # Alta afinidad → baja saturación temática; convertir a penalización
        theme_sat = 1.0 - avg_affinity
    else:
        theme_sat = 0.0   # con 1 publicación no hay secuencia que evaluar

    return 0.40 * time_sat + 0.30 * type_sat + 0.30 * theme_sat


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