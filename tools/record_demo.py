"""
Demo GIF kaydi - kayitli tohumlu bir oyunu oyunun kendi arayuzuyle cizer ve GIF yapar.

Kullanim (proje kokunden):
    python tools/record_demo.py                      # varsayilan: expectimax d=3, tohum 40
    python tools/record_demo.py --seed 94 --duration 15

Oyun cv_benchmark.py ile ayni tohumlama sirasiyla baslatilir ve oyunun kendi
GameManager / PygameRenderer siniflariyla, pencere acmadan (SDL dummy surucusu)
cizilir. Oyun bitince skor, en buyuk tas ve hamle sayisi results/ altindaki
kayitla karsilastirilir, uyusmazsa GIF uretilmez.

Kareler seyreltilir (her N. hamle). Sonda once oyunun bitmesinden hemen onceki
tahta (--hold-board), ardindan "Oyun Bitti!" ekrani (--hold-over) beklenir. GIF
ffmpeg ile iki gecisle (palettegen + paletteuse) uretilir ve boyut sinirini
asarsa daha kucuk genislikle tekrar denenir. ffmpeg PATH'te olmali ya da --ffmpeg ile
verilmeli. Sure olcmez, bu yuzden sonuc makineden bagimsizdir.
"""

import argparse
import csv
import math
import os
import random
import shutil
import subprocess
import sys
import tempfile

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('PYGAME_HIDE_SUPPORT_PROMPT', '1')

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
RESULTS = os.path.join(ROOT, 'experiments', 'results')

import numpy as np
import pygame

WIDTHS = [500, 400, 340]  # boyut siniri asilirsa sirayla denenir (pencere genisligi 500)


def recorded_game(agent, depth, seed):
    for name in ('games_main.csv', 'games_d5.csv'):
        with open(os.path.join(RESULTS, name), newline='') as f:
            for r in csv.DictReader(f):
                if r['agent'] == agent and int(r['depth']) == depth and int(r['seed']) == seed:
                    return int(r['score']), int(r['max_tile']), int(r['moves'])
    sys.exit(f'Kayit bulunamadi: {agent} d={depth} tohum={seed}')


def render_frames(agent_name, depth, seed, stride, frame_dir, board_frames, over_frames):
    """Oyunu oynatir, her `stride` hamlede bir kare kaydeder. Sonda son tahtayi `board_frames`,
    "Oyun Bitti!" ekranini `over_frames` kare tekrarlar. (skor, max tas, hamle, kare) dondurur."""
    from game.board import Board
    from game.game_manager import GameManager
    from modes.classic import ClassicMode
    from agents.alphabeta import AlphaBetaAgent
    from agents.expectimax import ExpectimaxAgent

    # cv_benchmark.py ile ayni sira: once tohum, sonra tahta, sonra ajan
    random.seed(seed)
    np.random.seed(seed)
    board = Board()
    cls = {'alphabeta': AlphaBetaAgent, 'expectimax': ExpectimaxAgent}[agent_name]
    agent = cls(depth=depth)

    game = GameManager(ClassicMode(board), agent=agent)
    game.auto_play = True
    frames = 0

    def save_frame(copies=1):
        nonlocal frames
        game.renderer.render(grid=game.mode.board.grid, status_text=game._get_status_text(),
                             game_over=game.mode.is_game_over())
        first = os.path.join(frame_dir, f'frame_{frames:05d}.png')
        pygame.image.save(game.renderer.screen, first)
        for _ in range(copies - 1):
            frames += 1
            shutil.copyfile(first, os.path.join(frame_dir, f'frame_{frames:05d}.png'))
        frames += 1

    save_frame()
    last_board = None
    # Oyundaki dongunun ajan kismi
    while not game.mode.is_game_over():
        before = board.copy()  # grid verildigi icin rastgele tas eklemez, tohum sirasi bozulmaz
        moves_before = agent.move_count
        game._agent_move()
        if agent.move_count == moves_before:
            break  # ajan hamle bulamadi
        if game.mode.is_game_over():
            last_board = before
        elif agent.move_count % stride == 0:
            save_frame()

    # Oyun bitmeden hemen onceki tahta, oyunda goruldugu haliyle ([AUTO] durumunda)
    if last_board is not None:
        game.mode = ClassicMode(last_board)
        save_frame(board_frames)
        game.mode = ClassicMode(board)
    # Oyunun kendi akisi: bir sonraki _agent_move oyun sonunu gorup auto_play'i kapatir
    game._agent_move()
    save_frame(over_frames)

    game.renderer.quit()
    return board.score, int(board.get_state()['max_tile']), agent.move_count, frames


def make_gif(ffmpeg, frame_dir, out_path, fps, width):
    graph = (f'scale={width}:-1:flags=lanczos,split[a][b];'
             f'[a]palettegen=stats_mode=diff[p];'
             f'[b][p]paletteuse=dither=bayer:bayer_scale=5:diff_mode=rectangle')
    subprocess.run([ffmpeg, '-y', '-loglevel', 'error', '-framerate', str(fps),
                    '-i', os.path.join(frame_dir, 'frame_%05d.png'),
                    '-filter_complex', graph, '-loop', '0', out_path], check=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--agent', choices=['expectimax', 'alphabeta'], default='expectimax')
    parser.add_argument('--depth', type=int, default=3)
    parser.add_argument('--seed', type=int, default=40)
    parser.add_argument('--duration', type=float, default=20.0, help='bekleme haric hedef sure (sn)')
    parser.add_argument('--fps', type=int, default=25)
    parser.add_argument('--hold-board', type=float, default=2.5, help='son tahtada bekleme (sn)')
    parser.add_argument('--hold-over', type=float, default=1.0, help='"Oyun Bitti!" ekraninda bekleme (sn)')
    parser.add_argument('--max-mb', type=float, default=5.0)
    parser.add_argument('--out', default=os.path.join(ROOT, 'docs', 'images', 'demo.gif'))
    parser.add_argument('--ffmpeg', default=shutil.which('ffmpeg'))
    args = parser.parse_args()

    if not args.ffmpeg:
        sys.exit('ffmpeg bulunamadi, PATH\'e ekleyin ya da --ffmpeg ile yolunu verin')

    want = recorded_game(args.agent, args.depth, args.seed)
    stride = max(1, math.ceil(want[2] / (args.duration * args.fps)))
    print(f'Kayit: skor={want[0]} max={want[1]} hamle={want[2]} -> her {stride}. hamle', flush=True)

    board_frames = max(1, round(args.hold_board * args.fps))
    over_frames = max(1, round(args.hold_over * args.fps))

    with tempfile.TemporaryDirectory() as frame_dir:
        *got, frames = render_frames(args.agent, args.depth, args.seed, stride, frame_dir,
                                     board_frames, over_frames)
        if tuple(got) != want:
            sys.exit(f'Oyun kayitla uyusmuyor: simdi {tuple(got)}, kayitli {want}. GIF uretilmedi.')
        print(f'Oyun kayitla ayni, {frames} kare cizildi', flush=True)

        os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
        for width in WIDTHS:
            make_gif(args.ffmpeg, frame_dir, args.out, args.fps, width)
            size_mb = os.path.getsize(args.out) / 2**20
            print(f'  genislik {width}px: {size_mb:.2f} MB', flush=True)
            if size_mb <= args.max_mb:
                break
        else:
            sys.exit(f'GIF {args.max_mb} MB sinirini asti, --duration ya da --fps dusurun')

    print(f'Kaydedildi: {args.out} ({frames} kare, ~{frames / args.fps:.1f} sn)')


if __name__ == '__main__':
    main()
