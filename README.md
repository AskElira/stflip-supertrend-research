# SuperTrend flip, 1h bias + lower-timeframe entry (NQ / MNQ research)

Idea: a higher-timeframe (HTF) SuperTrend flip sets the bias. A lower-timeframe (LTF) SuperTrend flip in the same
direction is the entry. Stop = LTF SuperTrend line at the entry flip. Exit = LTF flips back (or stop).
Variants: `first` = only the first LTF flip after an HTF flip; `every` = every LTF flip while the HTF trend agrees.

**Status: IN-SAMPLE research, no edge proven.** All NQ/MNQ history (2010-2026) was already read by earlier studies, so there is no unseen data.
Best variant (1h bias, 5m entry, ATR 10 x 3, every flip, 5m stop): MNQ 2019-2026 +$7,924 on 1 contract, 6,257 trades, t 1.65.
Neighbouring settings mostly lose money, so treat it as fragile. See `RESULTS.md`, `RESULTS_LUCID.md`, `variants_results.json`, `risk_sweep_results.json`.

## Files
- `stflip.py` - SuperTrend, timeframe pairs grid on NQ (36 pairs x 2 stops x 3 settings). `python stflip.py 10 3 out.json`
- `mnq_run.py` - one pair on MNQ with full trade list: `python mnq_run.py 1h 5m every`
- `variants.py` - 12 variants of the 1h/5m pair + LucidPro sim
- `lucid50.py`, `risk_sweep.py` - LucidPro 50K evaluation + funded simulation and risk-size sweep (rules assumed, listed in `RESULTS_LUCID.md`)
- `jelly_install.py` - local Jelly Charts importer (needs that app; ignore otherwise)

## To run
Needs 1-minute NQ/MNQ continuous parquet with columns `ts, real_open/high/low/close, cont_close` (Databento; **not included**, licensed).
Paths are hard-coded at the top of `stflip.py` (`ENG`) and `mnq_run.py` (`MNQ`). Python with pandas, numpy, polars.
