"""Backtest: using only inspections up to 2016, flag structures that would fall below BCI 60 by 2020.
Compare the trend-based flag with a condition-only baseline at equal flag counts."""
import json, numpy as np, pandas as pd
df = pd.read_pickle("out/bridges_clean.pkl")
Y = list(range(2008, 2017))
def latest(r, yrs):
    for y in reversed(yrs):
        if pd.notna(r[str(y)]): return r[str(y)]
    return np.nan
def slope(r):
    pts = [(y, r[str(y)]) for y in Y if pd.notna(r[str(y)])]
    for i in range(len(pts) - 1, 0, -1):
        if pts[i][1] - pts[i-1][1] > 5: pts = pts[i:]; break
    if len(pts) < 3 or pts[-1][0] - pts[0][0] < 4: return np.nan
    return np.polyfit([p[0] for p in pts], [p[1] for p in pts], 1)[0]
df["b16"] = df.apply(lambda r: latest(r, [2015, 2016]), axis=1)
df["b20"] = df.apply(lambda r: latest(r, [2019, 2020]), axis=1)
df["s16"] = df.apply(slope, axis=1)
d = df[(df.b16 >= 60) & df.b20.notna() & df.s16.notna()].copy()
d["pred20"] = d.b16 + 4.5 * d.s16
d["actual_poor"] = d.b20 < 60
trend_flag = d.pred20 < 60
k = int(trend_flag.sum())
base_flag = d.b16.rank(method="first") <= k   # same number of flags, lowest 2016 BCI
def m(flag):
    tp = int((flag & d.actual_poor).sum()); return {"flagged": int(flag.sum()), "correct": tp,
        "precision": round(tp / max(flag.sum(), 1), 3), "recall": round(tp / max(d.actual_poor.sum(), 1), 3)}
out = {"eligible": len(d), "became_poor_by_2020": int(d.actual_poor.sum()),
       "trend_model": m(trend_flag), "condition_only_baseline": m(base_flag),
       "mae_bci_2020": round(float((d.pred20 - d.b20).abs().median()), 2)}
json.dump(out, open("out/backtest.json", "w"), indent=1); print(json.dumps(out, indent=1))
