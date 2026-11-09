"""HTF SuperTrend flip arms the setup; LTF SuperTrend flip the same way = entry.
Stop = LTF (or HTF) SuperTrend line at the entry flip. Exit = LTF flips back (or stop).
IN-SAMPLE ONLY, NQ 2010-06..2026-08 is fully exposed: every result is an IS candidate, never a verdict."""
import sys, json, itertools
import numpy as np, pandas as pd, polars as pl
ENG = "/Users/alvin/AutonomouslyQuanting/engine/data/nq/parquet/continuous.parquet"
COST_PTS = 0.725   # NQ round trip: 2 x 1 tick slippage (0.5 pt) + $4.50 commission (0.225 pt)
TF = {"1m":1,"3m":3,"5m":5,"10m":10,"15m":15,"30m":30,"1h":60,"2h":120,"4h":240}

def load():
    d = pl.read_parquet(ENG).sort("ts").to_pandas()
    off = d["cont_close"] - d["real_close"]          # back-adjust OHLC by the per-bar roll offset
    for c in ("open","high","low","close"):
        d[c] = d["real_"+c] + off
    d["ts"] = d["ts"].dt.tz_convert("America/New_York").dt.tz_localize(None)
    d["off"] = off
    return d.set_index("ts")[["open","high","low","close","off"]]

def resample(m1, minutes):
    if minutes == 1: return m1
    r = m1.resample(f"{minutes}min", origin="start_day", offset="18h", label="left", closed="left").agg(
        {"open":"first","high":"max","low":"min","close":"last"}).dropna()
    return r

def supertrend(h, l, c, n=10, mult=3.0):
    N = len(c); d = np.zeros(N, np.int8); line = np.zeros(N)
    atr = 0.0; fu = fl = 0.0; dr = 1; pc = c[0]
    for i in range(N):
        tr = h[i]-l[i] if i == 0 else max(h[i]-l[i], abs(h[i]-pc), abs(l[i]-pc))
        atr = tr if i == 0 else (atr*(n-1)+tr)/n
        m = (h[i]+l[i])/2; bu = m+mult*atr; bl = m-mult*atr
        if i == 0: fu, fl = bu, bl
        else:
            fu = bu if (bu < fu or pc > fu) else fu
            fl = bl if (bl > fl or pc < fl) else fl
            if dr == 1 and c[i] < fl: dr = -1
            elif dr == -1 and c[i] > fu: dr = 1
        d[i] = dr; line[i] = fl if dr == 1 else fu; pc = c[i]
    return d, line

def build(m1, n, mult):
    out = {}
    for name, mins in TF.items():
        b = resample(m1, mins)
        d, ln = supertrend(b.high.values, b.low.values, b.close.values, n, mult)
        out[name] = dict(idx=b.index.values, mins=mins, o=b.open.values, h=b.high.values, l=b.low.values,
                         c=b.close.values, d=d, line=ln)
    return out

def simulate(H, L, stop_mode="ltf"):
    # HTF direction as known at each LTF bar close
    close_t = L["idx"] + np.timedelta64(L["mins"], "m")
    hclose = H["idx"] + np.timedelta64(H["mins"], "m")
    k = np.searchsorted(hclose, close_t, side="right") - 1
    ok = k >= 0
    dH = np.where(ok, H["d"][np.clip(k,0,None)], 0); lineH = np.where(ok, H["line"][np.clip(k,0,None)], 0.0)
    dL, lL, o, h, l = L["d"], L["line"], L["o"], L["h"], L["l"]
    N = len(dL); trades = []; armed = 0; pos = 0; warm = 300
    entry = stop = 0.0; ei = 0; pend = None
    for j in range(warm, N):
        if pend is not None:                       # entry at this bar's open
            side, st = pend; pend = None
            if (side == 1 and o[j] > st) or (side == -1 and o[j] < st):
                pos, entry, stop, ei = side, o[j], st, j
        if pos:                                     # stop check inside bar j
            if pos == 1 and l[j] <= stop: ex = min(stop, o[j]); hit = True
            elif pos == -1 and h[j] >= stop: ex = max(stop, o[j]); hit = True
            else: hit = False
            if hit:
                trades.append((L["idx"][ei], pos, entry, abs(entry-stop_init), ex, "S")); pos = 0
            elif dL[j] != pos:                       # LTF flipped against -> exit next open (use close as signal)
                if j+1 < N:
                    trades.append((L["idx"][ei], pos, entry, abs(entry-stop_init), o[j+1], "F")); pos = 0
        # setup logic at bar j close (HTF flip arms AFTER the LTF check so LTF flip must be strictly later)
        if pos == 0 and armed and dL[j] != dL[j-1] and dL[j] == armed and dH[j] == armed and j+1 < N:
            st = lL[j] if stop_mode == "ltf" else lineH[j]
            if (armed == 1 and st < o[j+1]) or (armed == -1 and st > o[j+1]):
                pend = (armed, st); stop_init = st
            armed = 0
        if dH[j] != dH[j-1] and dH[j-1] != 0 and dH[j] != 0: armed = int(dH[j])
    return trades

def stats(trades):
    if not trades: return None
    df = pd.DataFrame(trades, columns=["t","side","entry","risk","exit","how"])
    df["pts"] = (df.exit-df.entry)*df.side - COST_PTS
    df["R"] = df.pts/df.risk
    df["yr"] = pd.to_datetime(df.t).dt.year
    yrs = df.groupby("yr").pts.sum()
    blocks = {b: round(float(df[(df.yr>=a)&(df.yr<=z)].R.mean()), 3) if ((df.yr>=a)&(df.yr<=z)).any() else None
              for b,(a,z) in {"10-14":(2010,2014),"15-19":(2015,2019),"20-22":(2020,2022),"23-26":(2023,2026)}.items()}
    r = df.R.values
    t = r.mean()/(r.std(ddof=1)/np.sqrt(len(r))) if len(r) > 2 and r.std() > 0 else 0.0
    w, lo = r[r>0].sum(), -r[r<0].sum()
    return dict(n=len(df), per_yr=round(len(df)/16.2,1), win=round(float((r>0).mean()),3), avgR=round(float(r.mean()),3),
                t=round(float(t),2), pf=round(float(w/lo),2) if lo else None,
                netpts_tot=round(float(df.pts.sum()),0), yrs_pos=f"{int((yrs>0).sum())}/{len(yrs)}",
                long_avgR=round(float(df[df.side==1].R.mean()),3), short_avgR=round(float(df[df.side==-1].R.mean()),3),
                blocks=blocks, stop_pct=round(float((df.how=='S').mean()),2))

if __name__ == "__main__":
    n, mult = int(sys.argv[1]), float(sys.argv[2]); out = sys.argv[3]
    m1 = load(); T = build(m1, n, mult)
    names = list(TF); res = []
    for hn in names:
        for ln in names:
            if TF[ln] >= TF[hn]: continue
            for sm in ("ltf", "htf"):
                s = stats(simulate(T[hn], T[ln], sm))
                row = dict(htf=hn, ltf=ln, stop=sm, atr=n, mult=mult, **(s or {"n":0}))
                res.append(row); print(json.dumps(row), flush=True)
    json.dump(res, open(out, "w"), indent=1)
