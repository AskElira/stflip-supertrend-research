"""MNQ 2019-05..2026-08 full trade list for one pair (for Jelly Quant) + yearly summary."""
import sys, json, numpy as np, pandas as pd, polars as pl
import stflip as S
MNQ = "/Users/alvin/AutonomouslyQuanting/engine/data/parquet/continuous.parquet"
S.ENG = MNQ
SLIP_PTS, COMM_SIDE, PV = 0.25, 1.12, 2.0     # 1 tick/side, $1.12/side, MNQ $2/pt

def run(hn, ln, n=10, mult=3.0, stop_mode="ltf", every=False):
    m1 = S.load()
    S.TF = {k: v for k, v in S.TF.items() if k in (hn, ln)}
    T = S.build(m1, n, mult); H, L = T[hn], T[ln]
    close_t = L["idx"] + np.timedelta64(L["mins"], "m"); hclose = H["idx"] + np.timedelta64(H["mins"], "m")
    k = np.searchsorted(hclose, close_t, side="right") - 1
    dH = np.where(k >= 0, H["d"][np.clip(k, 0, None)], 0); lineH = np.where(k >= 0, H["line"][np.clip(k, 0, None)], 0.0)
    dL, lL, o, h, l = L["d"], L["line"], L["o"], L["h"], L["l"]; idx = L["idx"]
    N = len(dL); out = []; armed = pos = 0; pend = None; warm = 300
    for j in range(warm, N):
        if pend is not None:
            side, st = pend; pend = None
            if (side == 1 and o[j] > st) or (side == -1 and o[j] < st): pos, entry, stop, ei = side, o[j], st, j
        if pos:
            ex = None
            if pos == 1 and l[j] <= stop: ex, why, xi = min(stop, o[j]), "stop", j
            elif pos == -1 and h[j] >= stop: ex, why, xi = max(stop, o[j]), "stop", j
            elif dL[j] != pos and j+1 < N: ex, why, xi = o[j+1], "ltf_flip", j+1
            if ex is not None:
                out.append((ei, xi, pos, entry, stop, ex, why)); pos = 0
        if every: armed = int(dH[j])
        if pos == 0 and armed and dL[j] != dL[j-1] and dL[j] == armed and dH[j] == armed and j+1 < N:
            st = lL[j] if stop_mode == "ltf" else lineH[j]
            if (armed == 1 and st < o[j+1]) or (armed == -1 and st > o[j+1]): pend = (armed, st)
            armed = 0
        if dH[j] != dH[j-1] and dH[j-1] != 0 and dH[j] != 0: armed = int(dH[j])
    rows = []
    offs = m1["off"]
    for q, (ei, xi, side, en, st, ex, why) in enumerate(out, 1):
        oe, ox = float(offs.asof(pd.Timestamp(idx[ei]))), float(offs.asof(pd.Timestamp(idx[xi])))
        te = pd.Timestamp(idx[ei]).tz_localize("America/New_York", ambiguous="NaT", nonexistent="shift_forward")
        tx = pd.Timestamp(idx[xi]).tz_localize("America/New_York", ambiguous="NaT", nonexistent="shift_forward")
        if pd.isna(te) or pd.isna(tx): continue
        risk = abs(en - st); gross = (ex - en) * side
        net = (gross - 2*SLIP_PTS) * PV - 2*COMM_SIDE
        rows.append(dict(seq=q, direction="long" if side == 1 else "short", entry_ts=te.tz_convert("UTC").isoformat(),
            exit_ts=tx.tz_convert("UTC").isoformat(), session_date=str(te.date()), entry_price=float(en-oe), stop_price=float(st-oe),
            exit_price=float(ex-ox), exit_reason=why, risk_points=float(risk), pnl_dollars=round(float(net), 2),
            result_r=float(net/(risk*PV)), commission=2*COMM_SIDE))
    return rows

if __name__ == "__main__":
    hn, ln = sys.argv[1], sys.argv[2]
    ev = len(sys.argv) > 3; rows = run(hn, ln, every=ev); json.dump(rows, open(f"mnq_{hn}_{ln}{'_every' if ev else ''}.json", "w"))
    df = pd.DataFrame(rows); df["yr"] = pd.to_datetime(df.entry_ts).dt.year
    r = df.result_r
    print(f"{hn}->{ln} n={len(df)} win={(df.pnl_dollars>0).mean():.1%} net=${df.pnl_dollars.sum():,.0f} avgR={r.mean():.3f} t={r.mean()/(r.std()/len(r)**.5):.2f} PF={df.pnl_dollars[df.pnl_dollars>0].sum()/-df.pnl_dollars[df.pnl_dollars<0].sum():.2f}")
    print(df.groupby("yr").agg(n=("seq","count"), net=("pnl_dollars","sum"), avgR=("result_r","mean"), win=("pnl_dollars", lambda x:(x>0).mean())).round(3).to_string())
    print(df.groupby("direction").pnl_dollars.agg(["count","sum"]).to_string())
