# stflip pairs, 2026-11-09 — IN-SAMPLE EXPLORATION, NQ 2010-06..2026-08 (all exposed; no OOS exists)
Rule: HTF SuperTrend flips -> arm; first strictly-later LTF flip same way -> enter next open; stop = LTF line (or HTF line) at that flip; exit = LTF flips back or stop.
Costs 0.725 pt/round trip; OHLC back-adjusted by cont_close - real_close; ATR10/mult3 main grid, (10,2) and (14,4) as sensitivity.
36 pairs x 2 stops x 3 settings = 216 tries (counted, none dropped). Script: stflip.py. Raw: res_*.json, run_*.log.
Verdict: NO WIN. Main: 7/72 avg R>0, max t 0.80 (4h/5m, n=683, all from 2010-14). (10,2): 14/72 >0, max t 1.22. (14,4): 22/72 >0, max t 1.17. 0/216 reach t>=2.
Pairs with a 1m entry lose money (t down to -19): costs plus noise flips. Never pick a winner from these tables.
