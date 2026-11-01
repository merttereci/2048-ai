"""
Tekrar oynatma testi - kodun ajan hamlelerini degistirmedigini dogrular.

Kullanim (proje kokunden):
    python experiments/verify_replay.py          # hizli alt kume (427 oyun)
    python experiments/verify_replay.py --all    # results/ altindaki 730 oyunun hepsi

results/games_main.csv ve results/games_d5.csv'deki tohumlu oyunlari, cv_benchmark.py
ile ayni tohumlama sirasiyla yeniden oynatir ve skor, en buyuk tas ve hamle sayisini
kayitlarla karsilastirir. Sure olcmez, bu yuzden sonuc makineden bagimsizdir.
Herhangi bir oyun farkli cikarsa 1 koduyla cikar.
"""

import argparse
import csv
import os
import random
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
RESULTS = os.path.join(ROOT, 'experiments', 'results')

import numpy as np

# (ajan, derinlik, tohum sayisi). Hizli ayarlar tam, yavas ayarlar kismi.
QUICK = [
    ('expectimax', 2, 100), ('expectimax', 3, 100), ('expectimax', 4, 10),
    ('alphabeta', 3, 100), ('alphabeta', 4, 100), ('alphabeta', 5, 10),
    ('alphabeta', 6, 5), ('expectimax', 5, 2),
]


def load_recorded():
    recorded = {}
    for name in ('games_main.csv', 'games_d5.csv'):
        with open(os.path.join(RESULTS, name), newline='') as f:
            for r in csv.DictReader(f):
                key = (r['agent'], int(r['depth']), int(r['seed']))
                recorded[key] = (int(r['score']), int(r['max_tile']), int(r['moves']))
    return recorded


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--all', action='store_true', help='kayitli oyunlarin hepsini oynat')
    args = parser.parse_args()

    from game.board import Board
    from benchmark import run_single_game
    from agents.alphabeta import AlphaBetaAgent
    from agents.expectimax import ExpectimaxAgent
    classes = {'alphabeta': AlphaBetaAgent, 'expectimax': ExpectimaxAgent}

    recorded = load_recorded()
    if args.all:
        configs = {}
        for agent, depth, _ in recorded:
            configs[(agent, depth)] = configs.get((agent, depth), 0) + 1
        configs = [(a, d, n) for (a, d), n in configs.items()]
    else:
        configs = QUICK

    total = mismatched = 0
    for agent, depth, n_games in configs:
        bad = []
        for seed in range(n_games):
            random.seed(seed)
            np.random.seed(seed)
            board = Board()
            result = run_single_game(classes[agent](depth=depth), board)
            got = (result['score'], result['max_tile'], result['moves'])
            want = recorded[(agent, depth, seed)]
            total += 1
            if got != want:
                bad.append((seed, got, want))
        mismatched += len(bad)
        status = 'ayni' if not bad else f'{len(bad)} fark'
        print(f'{agent:10s} d={depth} tohum 0..{n_games - 1}: {status}', flush=True)
        for seed, got, want in bad[:5]:
            print(f'    tohum {seed}: simdi {got}, kayitli {want}', flush=True)

    print(f'\nToplam {total} / {len(recorded)} kayitli oyun oynatildi, {mismatched} fark')
    sys.exit(1 if mismatched else 0)


if __name__ == '__main__':
    main()
