import numpy as np
from collections import defaultdict
from core import Canvas, Color, ColorMove, LineCutMove, Orientation, PointCutMove, get_score, Move
from PIL import Image
from typing import Any, Dict, List

def pixelate(target_image: Image, initial_config: Dict[str, Any], max_block_size: int) -> List[Move]:
    image_width, image_height = target_image.size
    target_pixels = np.flip(np.array(target_image), 0)

    moves = []
    canvas = Canvas(initial_config)

    color_counts = defaultdict(int)
    for y in range(0, image_height, max_block_size):
        for x in range(0, image_width, max_block_size):
            block_width = min(image_width - x, max_block_size)
            block_height = min(image_height - y, max_block_size)

            common_r = np.argmax(np.bincount(target_pixels[y:y + block_height, x:x + block_width, 0].flatten()))
            common_g = np.argmax(np.bincount(target_pixels[y:y + block_height, x:x + block_width, 1].flatten()))
            common_b = np.argmax(np.bincount(target_pixels[y:y + block_height, x:x + block_width, 2].flatten()))
            common_a = np.argmax(np.bincount(target_pixels[y:y + block_height, x:x + block_width, 3].flatten()))

            color = Color(common_r, common_g, common_b, common_a)
            color_counts[color] += 1

    most_used_color = max(color_counts.keys(), key=lambda color: color_counts[color])
    moves.append(ColorMove("0", most_used_color))
    canvas.apply_move(moves[-1])

    for y in range(0, image_height, max_block_size):
        for x in range(0, image_width, max_block_size):
            block_width = min(image_width - x, max_block_size)
            block_height = min(image_height - y, max_block_size)

            block = canvas.get_block_by_pixel(x, y)

            if x + block_width < block.x + block.width and y + block_height < block.y + block.height:
                moves.append(PointCutMove(block.id, x + block_width, y + block_height))
                canvas.apply_move(moves[-1])
            elif x + block_width < block.x + block.width:
                moves.append(LineCutMove(block.id, Orientation.VERTICAL, x + block_width))
                canvas.apply_move(moves[-1])
            elif y + block_height < block.y + block.height:
                moves.append(LineCutMove(block.id, Orientation.HORIZONTAL, y + block_height))
                canvas.apply_move(moves[-1])

            block = canvas.get_block_by_pixel(x, y)

            common_r = np.argmax(np.bincount(target_pixels[y:y + block_height, x:x + block_width, 0].flatten()))
            common_g = np.argmax(np.bincount(target_pixels[y:y + block_height, x:x + block_width, 1].flatten()))
            common_b = np.argmax(np.bincount(target_pixels[y:y + block_height, x:x + block_width, 2].flatten()))
            common_a = np.argmax(np.bincount(target_pixels[y:y + block_height, x:x + block_width, 3].flatten()))

            color = Color(common_r, common_g, common_b, common_a)
            if color != most_used_color:
                moves.append(ColorMove(block.id, color))

    return moves

def run(target_image: Image, initial_config: Dict[str, Any]) -> List[Move]:
    canvas = Canvas(initial_config)
    if "0" not in canvas.blocks or canvas.blocks["0"].size != canvas.size:
        moves = []
        target_pixels = np.flip(np.array(target_image), 0)

        for block in canvas.blocks.values():
            mean_r = target_pixels[block.y:block.y + block.height, block.x:block.x + block.width, 0].mean()
            mean_g = target_pixels[block.y:block.y + block.height, block.x:block.x + block.width, 1].mean()
            mean_b = target_pixels[block.y:block.y + block.height, block.x:block.x + block.width, 2].mean()
            mean_a = target_pixels[block.y:block.y + block.height, block.x:block.x + block.width, 3].mean()

            color = Color(round(mean_r), round(mean_g), round(mean_b), round(mean_a))
            moves.append(ColorMove(block.id, color))

        return moves

    best_moves = []
    best_score = get_score(target_image, initial_config, best_moves)

    width, height = target_image.size
    for block_size in range(10, min(width, height) + 1, 10):
        moves = pixelate(target_image, block_size)
        score = get_score(target_image, initial_config, moves)
        if score < best_score:
            best_moves = moves
            best_score = score

    return best_moves
