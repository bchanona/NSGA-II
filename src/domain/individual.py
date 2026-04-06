import random
from src.domain.constants import MAX_PER_DAY

def random_individual(n_posts, types, hours, days):
    individual = []
    day_counts = {d: 0 for d in days}

    attempts = 0
    while len(individual) < n_posts and attempts < 1000:
        h = random.choice(hours)
        d = random.choice(days)
        t = random.choice(types)
        if day_counts[d] < MAX_PER_DAY:
            individual.append({'hour': h, 'day': d, 'type': t})
            day_counts[d] += 1
        attempts += 1

    return individual