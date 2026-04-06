def lookup_metrics(individual, knowledge):
    engagements, reaches, retentions = [], [], []
    for pub in individual:
        key = (pub['hour'], pub['day'], pub['type'])
        if key in knowledge:
            m = knowledge[key]
            factor = 1.0
        else:
            key = min(
                knowledge.keys(),
                key=lambda k: abs(k[0] - pub['hour']) + abs(k[1] - pub['day'])
            )
            m = knowledge[key]
            factor = 0.8
        engagements.append(m['engagement'] * factor)
        reaches.append(m['reach'] * factor)
        retentions.append(m['retention'] * factor)
    return engagements, reaches, retentions