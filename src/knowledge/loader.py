import pandas as pd

def load_knowledge(path, platform=None):
    kb = pd.read_csv(path)
    if platform:
        if 'platform' in kb.columns:
            kb = kb[kb['platform'] == platform]

    knowledge = {}
    for _, row in kb.iterrows():
        key = (int(row['hour']), int(row['day']), str(row['type']))
        knowledge[key] = {
            'engagement':  float(row['engagement']),
            'reach':       float(row['reach_score']),
            'retention':   float(row['retention']),
        }

    types    = sorted(kb['type'].unique().tolist())
    hours    = sorted(kb['hour'].unique().tolist())
    days     = sorted(kb['day'].unique().tolist())

    print(f"[KB] {len(knowledge)} combinaciones cargadas")
    print(f"     Tipos : {types}")
    print(f"     Horas : {hours[0]}–{hours[-1]}")
    print(f"     Días  : {days}")
    return knowledge, types, hours, days