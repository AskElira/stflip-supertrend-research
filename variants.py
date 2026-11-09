"""All 1h->5m variants on MNQ + LucidPro 50K sim. 12 variants, every one counted."""
import json, itertools, numpy as np, pandas as pd
import mnq_run as M, lucid50 as L
rows = []
for (n, mult), every, stop in itertools.product([(10, 3.0), (10, 2.0), (14, 4.0)], [False, True], ["ltf", "htf"]):
    tr = M.run("1h", "5m", n=n, mult=mult, stop_mode=stop, every=every)
    name = f"1h5m_n{n}_m{mult}_{'every' if every else 'first'}_{stop}"
    json.dump(tr, open(f"var_{name}.json", "w"))
    df = pd.DataFrame(tr); r = df.result_r; y = pd.to_datetime(df.entry_ts).dt.year
    h1, h2 = df[y <= 2022].pnl_dollars.sum(), df[y >= 2023].pnl_dollars.sum()
    row = dict(name=name, n=len(df), net=round(df.pnl_dollars.sum()), avgR=round(r.mean(), 3), t=round(r.mean()/(r.std()/len(r)**.5), 2),
               h1_net=round(h1), h2_net=round(h2))
    for risk in (200, 300):
        s = L.study(f"var_{name}.json", risk)
        row[f"r{risk}"] = (s["eval_pass"], s["eval_breach"], s["fund_any_payout"], s["fund_mean_cash"], s["fund_breach_1y"])
    rows.append(row); print(json.dumps(row), flush=True)
json.dump(rows, open("variants_results.json", "w"), indent=1)
