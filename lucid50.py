"""LucidPro 50K evaluation + funded simulation of the SuperTrend-flip trade lists (MNQ, 1 trade at a time).
IN-SAMPLE, rolling historical starts. Rules assumed (see RESULTS_LUCID.md): eval target $3,000, EOD trailing MLL $2,000
locking at $50,100 once an EOD balance reaches $52,100, soft DLL $1,200; funded same MLL, payout after cycle profit >= $500,
best day <= 40%, buffer $52,100, min request $500, caps $2,000 first / $2,500 after, 90% kept. Max 40 micros."""
import sys, json, numpy as np, pandas as pd
DIV = 3.0
START, MLL, LOCKAT, LOCKFLOOR, TARGET, DLL, CAP = 50000.0, 2000.0, 52100.0, 50100.0, 53000.0, 1200.0, 40
PV = 2.0

def load(f):
    d = pd.DataFrame(json.load(open(f)))
    d["day"] = (pd.to_datetime(d.exit_ts, utc=True).dt.tz_convert("America/New_York") + pd.Timedelta(hours=6)).dt.date
    return d[["day", "risk_points", "pnl_dollars"]].values.tolist()

def contracts(risk_pts, risk_usd):
    return min(CAP, int(risk_usd // (risk_pts * PV)))

class Acct:
    def __init__(s): s.bal = s.peak = START; s.floor = START - MLL; s.locked = False; s.dpnl = 0.0; s.best = 0.0; s.cyc = 0.0
    def eod(s):
        s.peak = max(s.peak, s.bal)
        if s.peak >= LOCKAT: s.floor, s.locked = LOCKFLOOR, True
        elif not s.locked: s.floor = s.peak - MLL

def run(trades, i0, risk, mode, max_days=252):
    """mode 'eval': returns (status, days). mode 'funded': returns (status, payouts, cash, days)."""
    a = Acct(); day = None; nd = 0; pays = 0; cash = 0.0; cyc_start = START; halted = False
    for k in range(i0, len(trades)):
        d, rp, pnl = trades[k]
        if d != day:
            if day is not None:
                a.eod(); nd += 1
                if mode == "eval" and a.bal >= TARGET: return "pass", nd
                if mode == "funded":
                    prof = a.bal - cyc_start
                    avail = a.bal - LOCKAT
                    if avail >= 500 and prof >= 500 and a.best <= 0.4 * prof:
                        amt = min(avail, 2000.0 if pays == 0 else 2500.0)
                        a.bal -= amt; cash += 0.9 * amt; pays += 1; cyc_start = a.bal; a.best = 0.0
                if nd >= max_days: return ("alive" if mode == "eval" else "alive"), (nd if mode == "eval" else (pays, cash, nd))
            day = d; a.dpnl = 0.0; halted = False
        if halted: continue
        r = min(risk, (a.bal - a.floor) / DIV)
        n = contracts(rp, r)
        if n < 1: continue
        p = pnl * n; a.bal += p; a.dpnl += p
        a.best = max(a.best, a.dpnl)
        if a.bal <= a.floor: return ("breach", nd) if mode == "eval" else ("breach", (pays, cash, nd))
        if a.dpnl <= -DLL: halted = True
    return ("end", nd) if mode == "eval" else ("end", (pays, cash, nd))

def study(f, risk):
    T = load(f); days = sorted({t[0] for t in T}); first_idx = {}
    for i, t in enumerate(T): first_idx.setdefault(t[0], i)
    starts = [first_idx[d] for d in days[::5]]
    ev = [run(T, i, risk, "eval", 400) for i in starts]
    fu = [run(T, i, risk, "funded", 252) for i in starts]
    ev = [e for e in ev if e[0] != "end"]; fu = [x for x in fu if x[0] != "end"]
    ne = len(ev); passed = [e for e in ev if e[0] == "pass"]; br = sum(e[0] == "breach" for e in ev)
    nf = len(fu); fb = sum(x[0] == "breach" for x in fu); fp = [x[1] for x in fu]
    return dict(file=f, risk=risk, eval_n=ne, eval_pass=round(len(passed)/ne, 3), eval_breach=round(br/ne, 3),
        eval_med_days=int(np.median([e[1] for e in passed])) if passed else None,
        fund_n=nf, fund_breach_1y=round(fb/nf, 3), fund_any_payout=round(np.mean([p[0] > 0 for p in fp]), 3),
        fund_med_payouts=float(np.median([p[0] for p in fp])), fund_mean_cash=round(float(np.mean([p[1] for p in fp])), 0),
        fund_median_cash=round(float(np.median([p[1] for p in fp])), 0))

if __name__ == "__main__":
    out = []
    for f in ["mnq_1h_5m_every.json", "mnq_1h_15m_every.json", "mnq_1h_15m.json"]:
        for risk in (100, 200, 300, 400):
            r = study(f, risk); out.append(r); print(json.dumps(r), flush=True)
    json.dump(out, open("lucid50_results.json", "w"), indent=1)
