# LucidPro 50K simulation of the SuperTrend-flip trade lists (MNQ 2019-05..2026-08, IN-SAMPLE, rolling starts every 5 sessions)
Assumed rules (eval target/MLL not in local docs; inferred from the 150K model + funded 50K docs): eval target $3,000, EOD trailing MLL $2,000 locking at $50,100 after EOD >= $52,100, soft DLL $1,200, <=40 micros, no eval consistency.
Funded (from lucid50k_funded_to_live_20261009/rules): buffer $52,100, min request $500, cycle profit >= $500, best day <= 40%, caps $2,000 first / $2,500 after, 90% kept. Sizing: risk = min(fixed $, cushion/3), whole micros.
Eval: up to 400 sessions per start. Funded: 252 sessions per start, payout requested at the first eligible EOD. Fees (eval, reset) not modelled. Costs = 1 tick/side + $1.12/side per micro.
Results: lucid50_results.json. Script: lucid50.py. Not a verdict: no unseen data.
