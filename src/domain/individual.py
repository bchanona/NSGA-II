import random
from src.domain.constants import MAX_PER_DAY

# Temas disponibles para la secuencia temática
THEMES = ['educativo', 'entretenimiento', 'promocional', 'inspiracional', 'tutorial']

# Reglas de coherencia temática: qué temas combinan bien en secuencia
# Un tema que aparece después de otro con alta frecuencia reduce la retención
THEME_AFFINITY = {
    'educativo':      {'educativo': 0.5, 'tutorial': 0.9, 'entretenimiento': 0.8, 'inspiracional': 0.7, 'promocional': 0.4},
    'entretenimiento':{'educativo': 0.8, 'tutorial': 0.6, 'entretenimiento': 0.4, 'inspiracional': 0.9, 'promocional': 0.7},
    'promocional':    {'educativo': 0.7, 'tutorial': 0.8, 'entretenimiento': 0.9, 'inspiracional': 0.6, 'promocional': 0.3},
    'inspiracional':  {'educativo': 0.9, 'tutorial': 0.7, 'entretenimiento': 0.8, 'inspiracional': 0.4, 'promocional': 0.6},
    'tutorial':       {'educativo': 0.9, 'tutorial': 0.5, 'entretenimiento': 0.7, 'inspiracional': 0.8, 'promocional': 0.6},
}


def random_individual(n_posts, types, hours, days):
    """
    Genera un individuo aleatorio.
    Cada publicación incluye ahora el campo 'theme' (sᵢ),
    que representa la secuencia temática del contenido.
    """
    individual = []
    day_counts = {d: 0 for d in days}

    attempts = 0
    while len(individual) < n_posts and attempts < 1000:
        h = random.choice(hours)
        d = random.choice(days)
        t = random.choice(types)
        s = random.choice(THEMES)          

        if day_counts[d] < MAX_PER_DAY:
            individual.append({'hour': h, 'day': d, 'type': t, 'theme': s})
            day_counts[d] += 1
        attempts += 1

    return individual