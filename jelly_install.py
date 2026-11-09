"""Put the MNQ trade lists into Jelly Quant on Jelly's own contract prices (no roll-mismatch banner)."""
import json, sys
sys.path.insert(0, '/Users/alvin/Desktop/Jelly Charts')
from pathlib import Path
import pandas as pd
from backend.app.data import BarStore
from backend.app.quant_store import QuantStore
D = '/Users/alvin/AutonomouslyQuanting/quantlab/stflip_pairs_20261109/'
eng = pd.read_parquet('/Users/alvin/AutonomouslyQuanting/engine/data/parquet/continuous.parquet', columns=['ts', 'real_close'])
eng = eng.set_index('ts')['real_close']; eng = eng[~eng.index.duplicated()]
jel = BarStore('MNQ').load_1m(pd.Timestamp('2019-05-01', tz='UTC'), pd.Timestamp('2026-08-26', tz='UTC'))
jel = jel[~jel.index.duplicated()]
def at(ts):
    t = pd.Timestamp(ts)
    return float(jel.close.asof(t)), str(jel.symbol.asof(t)), float(eng.asof(t))
s = QuantStore(Path('/Users/alvin/Desktop/Jelly Charts/data/db/jelly.db'))
for st in s.list_strategies():
    if st['source_kind'].startswith('external:stflip-') and st['source_kind'].endswith('-v2'): s.archive_strategy(st['id'])
jobs = [('mnq_1h_15m.json','1h','15m','first 15m flip after a 1h flip','ST flip · 1h arms, 15m enters (MNQ)','first15'),
        ('mnq_1h_15m_every.json','1h','15m','every 15m flip while 1h trend agrees','ST flip · every 15m flip with 1h bias (MNQ)','every15'),
        ('mnq_1h_5m_every.json','1h','5m','every 5m flip while 1h trend agrees','ST flip · every 5m flip with 1h bias (MNQ)','every5')]
for f, h, l, entry, name, key in jobs:
    rows = json.load(open(D + f)); moved = 0
    for r in rows:
        jc, sym, ec = at(r['entry_ts']); de = jc - ec
        xc, _, xe = at(r['exit_ts']); dx = xc - xe
        if abs(de) > 0.01 or abs(dx) > 0.01: moved += 1
        r['entry_price'] += de; r['stop_price'] += de; r['exit_price'] += dx
        r.update(symbol=sym, quantity=1, entry_tag=f'{l} SuperTrend flip with {h} trend', target_price=None, exit_count=1,
                 exits=[{'ts': r['exit_ts'], 'price': r['exit_price'], 'quantity': 1, 'reason': r['exit_reason']}],
                 mfe_r=None, mae_r=None, orphan_bracket_entry=False)
    st = s.ensure_strategy(name=name, module=f'external.stflip_{key}_v3', class_name='FrozenLedger',
        params={'atr': 10, 'mult': 3.0, 'htf': h, 'ltf': l, 'entry': entry, 'stop': f'{l} SuperTrend line at entry flip', 'exit': f'{l} flips back'},
        notes='IN-SAMPLE research replay only, on Jelly contract prices. stflip_pairs_20261109/jelly_install.py. 1 MNQ, 1 tick/side, $1.12/side.',
        source_kind=f'external:stflip-{key}-mnq-v3')
    s.set_view(st['id'], {'indicators': [{'key': 'supertrend', 'params': {'period': 10, 'mult': 3.0}, 'tf': h, 'label': f'ST {h}', 'color': '#3b82f6'},
                                         {'key': 'supertrend', 'params': {'period': 10, 'mult': 3.0}, 'tf': l, 'label': f'ST {l}', 'color': '#f59e0b'}]})
    cfg = {'window': {'start': '2019-05-06', 'end': '2026-08-24'}, 'strategy': {'module': f'external.stflip_{key}_v3', 'class_name': 'FrozenLedger', 'params': {}}, 'execution': {'slippage_ticks': 1, 'commission_per_side': 1.12, 'contract': 'MNQ'}, 'seed': 0}
    run = s.save_run(st['id'], 'MNQ', cfg, {'run_id': 'external-stflip-' + key, 'final_balance': None, 'bars_processed': 0, 'halt_reason': None}, rows, label=f'{h} bias / {l} · MNQ 2019–2026')
    print(name, st['id'], run['id'], 'trades with a roll-price fix:', moved, s.run_summary(run['id'])['net_dollars'])
