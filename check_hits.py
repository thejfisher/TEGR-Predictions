
import json
with open('double_slit_results.json', 'r') as f:
    data = json.load(f)
    if isinstance(data, dict):
        keys = list(data.keys())
        for k in keys[-25:]:
            r = data[k]
            m = r.get('m', 1)
            p = r.get('momentum_p', 0)
            hits = r.get('total_hits', 0)
            print(f'Mass: {m}, Date: {r.get("timestamp")}, Hit Rate: {hits} ({hits/10000*100:.2f}%), V: {p/m if m else "?"}')

