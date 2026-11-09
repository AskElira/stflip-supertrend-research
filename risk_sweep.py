import json, itertools
import lucid50 as L
rows = []
for div, risk in itertools.product([2.0, 3.0, 5.0], [100, 150, 200, 250, 300, 400, 500, 600, 800, 1000]):
    L.DIV = div
    s = L.study("mnq_1h_5m_every.json", risk); s["div"] = div; rows.append(s)
    print(json.dumps({k: s[k] for k in ("div","risk","eval_pass","eval_breach","eval_med_days","fund_any_payout","fund_med_payouts","fund_mean_cash","fund_median_cash","fund_breach_1y")}), flush=True)
json.dump(rows, open("risk_sweep_results.json", "w"), indent=1)
