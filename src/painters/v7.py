import numpy as np
from copy import deepcopy
from core import Block, Canvas, Color, ColorMove, LineCutMove, Move, Orientation, get_score
from painters.v6 import run as v6
from PIL import Image
from scipy import stats
from typing import Any, Dict, List

def process(target_image: Image, canvas: Canvas, bounds: Block, min_bar_size: int, bar_orientation: Orientation) -> List[Move]:
    target_pixels = np.flip(np.array(target_image), 0)

    bars = []
    position = bounds.x if bar_orientation == Orientation.VERTICAL else bounds.y
    max_position = bounds.width if bar_orientation == Orientation.VERTICAL else bounds.height
    while position < max_position:
        bar_start = position
        bar_size = min(min_bar_size, max_position - position)

        if bar_orientation == Orientation.VERTICAL:
            bar_pixels = target_pixels[bounds.y:bounds.y + bounds.height, position:position + bar_size, :].reshape(-1, 4)
        else:
            bar_pixels = target_pixels[position:position + bar_size, bounds.x:bounds.x + bounds.height, :].reshape(-1, 4)

        bar_color = stats.mode(bar_pixels, keepdims=False).mode
        bars.append([bar_color, bar_start, bar_size])

        position += bar_size

    merged_bars = []
    for bar in bars:
        if len(merged_bars) > 0 and np.array_equal(merged_bars[-1][0], bar[0]):
            merged_bars[-1][2] += bar[2]
        else:
            merged_bars.append(bar.copy())

    moves = []

    for bar_color, bar_start, bar_size in merged_bars:
        if bar_orientation == Orientation.VERTICAL:
            block = canvas.get_block_by_pixel(bar_start, bounds.y)
        else:
            block = canvas.get_block_by_pixel(bounds.x, bar_start)

        if bar_orientation == Orientation.VERTICAL and block.width != bar_size:
            moves.append(LineCutMove(block.id, Orientation.VERTICAL, bar_start + bar_size))
            canvas.apply_move(moves[-1])
            block = canvas.get_block_by_pixel(bar_start, bounds.y)
        elif bar_orientation == Orientation.HORIZONTAL and block.height != bar_size:
            moves.append(LineCutMove(block.id, Orientation.HORIZONTAL, bar_start + bar_size))
            canvas.apply_move(moves[-1])
            block = canvas.get_block_by_pixel(bounds.x, bar_start)

        moves.append(ColorMove(block.id, Color(*bar_color)))

    return moves

def run(target_image: Image, initial_config: Dict[str, Any]) -> List[Move]:
    canvas = Canvas(initial_config)
    if "0" not in canvas.blocks or canvas.blocks["0"].size != canvas.size:
        return v6(target_image, initial_config)

    width, height = target_image.size

    best_moves = []
    best_score = get_score(target_image, initial_config, best_moves)

    block_queue = list(canvas.blocks.keys())
    while len(block_queue) > 0:
        bounds = canvas.get_block_by_id(block_queue.pop(0))

        possible_moves = []

        for min_bar_size in range(1, width + 1):
            canvas_copy = deepcopy(canvas)
            possible_moves.append((canvas_copy, process(target_image, canvas_copy, bounds, min_bar_size, Orientation.VERTICAL)))

        for min_bar_size in range(1, height + 1):
            canvas_copy = deepcopy(canvas)
            possible_moves.append((canvas_copy, process(target_image, canvas_copy, bounds, min_bar_size, Orientation.HORIZONTAL)))

        local_canvas = canvas
        local_moves = best_moves
        local_score = best_score

        for canvas_copy, moves in possible_moves:
            score = get_score(target_image, initial_config, best_moves + moves)
            if score < local_score:
                local_canvas = canvas_copy
                local_moves = best_moves + moves
                local_score = score

        for block_id in local_canvas.blocks.keys():
            if block_id not in canvas.blocks:
                block_queue.append(block_id)

        canvas = local_canvas
        best_moves = local_moves
        best_score = local_score

    return best_moves
