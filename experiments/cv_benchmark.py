"""
CV benchmark - oyun kodunu degistirmeden, sadece olcum yapan betik.

Kullanim (proje kokunden, D:\\2048):
    python experiments/cv_benchmark.py sysinfo
    python experiments/cv_benchmark.py speedup
    python experiments/cv_benchmark.py games --phase main
    python experiments/cv_benchmark.py games --phase d5
    python experiments/cv_benchmark.py summarize

Ciktilar experiments/results/ altina yazilir.

Notlar:
- Her oyun, oyun numarasi kadar tohumla baslar (0, 1, 2, ...). Hem `random`
  hem `numpy.random` her oyundan once tohumlanir. Board sadece `random`
  kullanir; numpy tohumu istek uzerine ayrica atilir.
- Ajanlar deterministik oldugundan ayni tohum + ayni ajan/derinlik = ayni oyun.
- Ajanin kendi `thinking_time` sayaci time.time() kullanir (Windows'ta ~15.6 ms
  cozunurluk). Bu yuzden ayrica time.perf_counter() ile duvar saati olculur.
"""

import argparse
import csv
import ctypes
import hashlib
import json
import os
import platform
import random
import statistics
import subprocess
import sys
import time
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
RESULTS = os.path.join(ROOT, 'experiments', 'results')

import numpy as np

PHASES = {
    'main': [
        ('expectimax', 2, 100),
        ('expectimax', 3, 100),
        ('expectimax', 4, 100),
        ('alphabeta', 3, 100),
        ('alphabeta', 4, 100),
        ('alphabeta', 5, 100),
        ('alphabeta', 6, 100),
    ],
    'd5': [
        ('expectimax', 5, 30),
    ],
}

SPEEDUP_SEEDS = [1, 2, 3]
SPEEDUP_DEPTH = 3
SPEEDUP_MOVES = 30
WARMUP_MOVES = 5

TILE_THRESHOLDS = [1024, 2048, 4096, 8192]

SOURCE_FILES = [
    'benchmark.py', 'constants.py',
    'game/board.py', 'game/logic.py',
    'agents/base_agent.py', 'agents/heuristics.py',
    'agents/alphabeta.py', 'agents/expectimax.py',
]


def agent_class(name):
    from agents.alphabeta import AlphaBetaAgent
    from agents.expectimax import ExpectimaxAgent
    return {'alphabeta': AlphaBetaAgent, 'expectimax': ExpectimaxAgent}[name]


def seed_all(seed):
    random.seed(seed)
    np.random.seed(seed)


def keep_awake():
    """Bu surec calistigi surece Windows'un uykuya gecmesini engelle."""
    if sys.platform == 'win32':
        ES_CONTINUOUS, ES_SYSTEM_REQUIRED = 0x80000000, 0x00000001
        ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS | ES_SYSTEM_REQUIRED)


def on_ac_power():
    if sys.platform != 'win32':
        return None

    class SYSTEM_POWER_STATUS(ctypes.Structure):
        _fields_ = [('ACLineStatus', ctypes.c_byte), ('BatteryFlag', ctypes.c_byte),
                    ('BatteryLifePercent', ctypes.c_byte), ('SystemStatusFlag', ctypes.c_byte),
                    ('BatteryLifeTime', ctypes.c_ulong), ('BatteryFullLifeTime', ctypes.c_ulong)]

    status = SYSTEM_POWER_STATUS()
    ctypes.windll.kernel32.GetSystemPowerStatus(ctypes.byref(status))
    return {0: False, 1: True}.get(status.ACLineStatus)


def cpu_name():
    if sys.platform == 'win32':
        import winreg
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                             r'HARDWARE\DESCRIPTION\System\CentralProcessor\0')
        return winreg.QueryValueEx(key, 'ProcessorNameString')[0].strip()
    return platform.processor()


def source_hashes():
    hashes = {}
    for rel in SOURCE_FILES:
        with open(os.path.join(ROOT, rel), 'rb') as f:
            hashes[rel] = hashlib.sha256(f.read()).hexdigest()
    return hashes


def warm_up():
    """Numba derlemesini olcumden once tetikle (birkac hamle)."""
    from game.board import Board
    t = time.perf_counter()
    for name in ('alphabeta', 'expectimax'):
        agent = agent_class(name)(depth=2)
        board = Board()
        for _ in range(WARMUP_MOVES):
            move = agent.get_move(board)
            if move is None:
                break
            board.move(move)
    return time.perf_counter() - t


# ---------------------------------------------------------------- sysinfo

def cmd_sysinfo(args):
    import numba
    import llvmlite
    info = {
        'timestamp': datetime.now().isoformat(timespec='seconds'),
        'cpu': cpu_name(),
        'logical_cpus': os.cpu_count(),
        'os': platform.platform(),
        'python': platform.python_version(),
        'numpy': np.__version__,
        'numba': numba.__version__,
        'llvmlite': llvmlite.__version__,
        'ac_power': on_ac_power(),
        'clock_time': str(time.get_clock_info('time')),
        'clock_perf_counter': str(time.get_clock_info('perf_counter')),
        'source_sha256': source_hashes(),
    }
    os.makedirs(RESULTS, exist_ok=True)
    with open(os.path.join(RESULTS, 'sysinfo.json'), 'w', encoding='utf-8') as f:
        json.dump(info, f, indent=2)
    print(json.dumps(info, indent=2))


# ---------------------------------------------------------------- games

def cmd_games(args):
    from game.board import Board
    from benchmark import run_single_game

    keep_awake()
    os.makedirs(RESULTS, exist_ok=True)
    out_path = os.path.join(RESULTS, f'games_{args.phase}.csv')

    print(f'[{datetime.now():%H:%M:%S}] phase={args.phase} ac_power={on_ac_power()} '
          f'sha256_ok={source_hashes() == _recorded_hashes()}', flush=True)
    print(f'warm-up (compile): {warm_up():.1f}s', flush=True)

    fields = ['agent', 'depth', 'seed', 'score', 'max_tile', 'moves',
              'wall_time_s', 'agent_time_s']
    with open(out_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for name, depth, n_games in PHASES[args.phase]:
            cls = agent_class(name)
            cfg_start = time.perf_counter()
            for seed in range(n_games):
                seed_all(seed)
                board = Board()
                agent = cls(depth=depth)
                t = time.perf_counter()
                result = run_single_game(agent, board)
                wall = time.perf_counter() - t
                writer.writerow({
                    'agent': name, 'depth': depth, 'seed': seed,
                    'score': result['score'], 'max_tile': result['max_tile'],
                    'moves': result['moves'],
                    'wall_time_s': f'{wall:.6f}',
                    'agent_time_s': f"{result['time']:.6f}",
                })
                f.flush()
                print(f'  {name} d={depth} seed={seed:3d}: score={result["score"]:7d} '
                      f'max={result["max_tile"]:5d} moves={result["moves"]:5d} wall={wall:8.2f}s',
                      flush=True)
            print(f'[{datetime.now():%H:%M:%S}] done {name} d={depth} '
                  f'({time.perf_counter() - cfg_start:.0f}s)', flush=True)
    print(f'ac_power at end={on_ac_power()}', flush=True)


def _recorded_hashes():
    path = os.path.join(RESULTS, 'sysinfo.json')
    if not os.path.exists(path):
        return None
    with open(path, encoding='utf-8') as f:
        return json.load(f)['source_sha256']


# ---------------------------------------------------------------- speedup

def cmd_speedup(args):
    """JIT acik ve kapali iki ayri surec calistir (env degiskeni import oncesi gerekli)."""
    os.makedirs(RESULTS, exist_ok=True)
    out_path = os.path.join(RESULTS, 'speedup_moves.csv')
    if os.path.exists(out_path):
        os.remove(out_path)
    for jit in ('on', 'off'):
        env = dict(os.environ)
        env.pop('NUMBA_DISABLE_JIT', None)
        if jit == 'off':
            env['NUMBA_DISABLE_JIT'] = '1'
        subprocess.run([sys.executable, os.path.abspath(__file__), 'speedup-worker'],
                       env=env, check=True)


def cmd_speedup_worker(args):
    from game.board import Board

    keep_awake()
    jit = 'off' if os.environ.get('NUMBA_DISABLE_JIT') == '1' else 'on'
    print(f'speedup worker JIT={jit}, warm-up {warm_up():.1f}s', flush=True)

    out_path = os.path.join(RESULTS, 'speedup_moves.csv')
    new_file = not os.path.exists(out_path)
    with open(out_path, 'a', newline='') as f:
        writer = csv.writer(f)
        if new_file:
            writer.writerow(['jit', 'agent', 'depth', 'seed', 'move_idx', 'move', 'time_s'])
        for name in ('expectimax', 'alphabeta'):
            for seed in SPEEDUP_SEEDS:
                seed_all(seed)
                board = Board()
                agent = agent_class(name)(depth=SPEEDUP_DEPTH)
                for i in range(SPEEDUP_MOVES):
                    t = time.perf_counter()
                    move = agent.get_move(board)
                    dt = time.perf_counter() - t
                    if move is None:
                        break
                    board.move(move)
                    writer.writerow([jit, name, SPEEDUP_DEPTH, seed, i, move, f'{dt:.9f}'])
                print(f'  JIT={jit} {name} seed={seed} done', flush=True)


# ---------------------------------------------------------------- summarize

def read_games():
    rows = []
    for phase in PHASES:
        path = os.path.join(RESULTS, f'games_{phase}.csv')
        if os.path.exists(path):
            with open(path, newline='') as f:
                rows.extend(csv.DictReader(f))
    return rows


def cmd_summarize(args):
    rows = read_games()
    configs = [(a, d) for phase in PHASES.values() for a, d, _ in phase]
    lines = []
    header = ('| Ajan | d | Oyun | Ort. skor | Medyan | Min | Max | '
              + ' | '.join(f'>={t}' for t in TILE_THRESHOLDS)
              + ' | Sure/oyun (s) | Sure/hamle (ms) | Ort. hamle |')
    lines.append(header)
    lines.append('|' + '---|' * (header.count('|') - 1))
    summary_rows = []
    for agent, depth in configs:
        games = [r for r in rows if r['agent'] == agent and int(r['depth']) == depth]
        if not games:
            continue
        scores = [int(r['score']) for r in games]
        tiles = [int(r['max_tile']) for r in games]
        moves = [int(r['moves']) for r in games]
        wall = [float(r['wall_time_s']) for r in games]
        n = len(games)
        pct = {t: 100.0 * sum(x >= t for x in tiles) / n for t in TILE_THRESHOLDS}
        s = {
            'agent': agent, 'depth': depth, 'games': n,
            'mean_score': statistics.mean(scores), 'median_score': statistics.median(scores),
            'min_score': min(scores), 'max_score': max(scores),
            **{f'pct_ge_{t}': pct[t] for t in TILE_THRESHOLDS},
            'mean_game_time_s': statistics.mean(wall),
            'ms_per_move': 1000.0 * sum(wall) / sum(moves),
            'mean_moves': statistics.mean(moves),
        }
        summary_rows.append(s)
        lines.append(
            f"| {agent} | {depth} | {n} | {s['mean_score']:,.0f} | {s['median_score']:,.0f} | "
            f"{s['min_score']:,} | {s['max_score']:,} | "
            + ' | '.join(f'{pct[t]:.0f}%' for t in TILE_THRESHOLDS)
            + f" | {s['mean_game_time_s']:.2f} | {s['ms_per_move']:.3f} | {s['mean_moves']:.0f} |")

    # Max tile dagilimi
    lines.append('')
    lines.append('Max tile dagilimi (oyun sayisi):')
    for agent, depth in configs:
        tiles = [int(r['max_tile']) for r in rows if r['agent'] == agent and int(r['depth']) == depth]
        if tiles:
            dist = {t: tiles.count(t) for t in sorted(set(tiles), reverse=True)}
            lines.append(f'  {agent} d={depth}: ' + ', '.join(f'{t}: {c}' for t, c in dist.items()))

    sp_path = os.path.join(RESULTS, 'speedup_moves.csv')
    if os.path.exists(sp_path):
        with open(sp_path, newline='') as f:
            sp = list(csv.DictReader(f))
        lines.append('')
        lines.append(f'| Numba (d={SPEEDUP_DEPTH}, tohum {SPEEDUP_SEEDS}, ilk {SPEEDUP_MOVES} hamle) '
                     '| JIT acik ms/hamle | JIT kapali ms/hamle | Oran | Hamle dizileri ayni |')
        lines.append('|---|---|---|---|---|')
        for agent in ('expectimax', 'alphabeta'):
            on = [r for r in sp if r['agent'] == agent and r['jit'] == 'on']
            off = [r for r in sp if r['agent'] == agent and r['jit'] == 'off']
            if not on or not off:
                continue
            t_on = 1000 * sum(float(r['time_s']) for r in on) / len(on)
            t_off = 1000 * sum(float(r['time_s']) for r in off) / len(off)
            same = [(r['seed'], r['move']) for r in on] == [(r['seed'], r['move']) for r in off]
            lines.append(f'| {agent} | {t_on:.3f} | {t_off:.3f} | {t_off / t_on:.1f}x | {same} |')

    text = '\n'.join(lines)
    print(text)
    with open(os.path.join(RESULTS, 'summary.md'), 'w', encoding='utf-8') as f:
        f.write(text + '\n')
    if summary_rows:
        with open(os.path.join(RESULTS, 'summary.csv'), 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=list(summary_rows[0].keys()))
            writer.writeheader()
            writer.writerows(summary_rows)


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest='cmd', required=True)
    sub.add_parser('sysinfo')
    sub.add_parser('speedup')
    sub.add_parser('speedup-worker')
    g = sub.add_parser('games')
    g.add_argument('--phase', choices=list(PHASES), required=True)
    sub.add_parser('summarize')
    args = parser.parse_args()
    {
        'sysinfo': cmd_sysinfo, 'speedup': cmd_speedup, 'speedup-worker': cmd_speedup_worker,
        'games': cmd_games, 'summarize': cmd_summarize,
    }[args.cmd](args)


if __name__ == '__main__':
    main()
