import random
from src.domain.constants import MAX_PER_DAY

def repair(individual, types, hours, days):
    day_counts = {d: 0 for d in days}
    valid   = []
    pending = []

    for pub in individual:
        if day_counts.get(pub['day'], 0) < MAX_PER_DAY:
            valid.append(pub)
            day_counts[pub['day']] = day_counts.get(pub['day'], 0) + 1
        else:
            pending.append(pub)

    for pub in pending:
        free_days = [d for d in days if day_counts.get(d, 0) < MAX_PER_DAY]
        if free_days:
            pub['day'] = random.choice(free_days)
            day_counts[pub['day']] += 1
            valid.append(pub)

    return valid