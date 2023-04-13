import numpy as np
from core import Canvas, Color, ColorMove, LineCutMove, Orientation, get_score, Move
from PIL import Image
from typing import Any, Dict, List

def pixelate(target_image: Image, initial_config: Dict[str, any], block_size: int) -> List[Move]:
    image_width, image_height = target_image.size
    target_pixels = np.flip(np.array(target_image), 1)

    moves = []
    canvas = Canvas(initial_config)

    for y in range(0, image_height, block_size):
        for x in range(0, image_width, block_size):
            block_width = min(image_width - x, block_size)
            block_height = min(image_height - y, block_size)

            block = canvas.get_block_by_pixel(x, y)

            if x + block_width < block.x + block.width:
                moves.append(LineCutMove(block.id, Orientation.VERTICAL, x + block_width))
                canvas.apply_move(moves[-1])
                block = canvas.get_block_by_pixel(x, y)

            if y + block_height < block.y + block.height:
                moves.append(LineCutMove(block.id, Orientation.HORIZONTAL, y + block_height))
                canvas.apply_move(moves[-1])
                block = canvas.get_block_by_pixel(x, y)

            mean_r = target_pixels[x:x + block_width, y:y + block_height, 0].mean()
            mean_g = target_pixels[x:x + block_width, y:y + block_height, 1].mean()
            mean_b = target_pixels[x:x + block_width, y:y + block_height, 2].mean()
            mean_a = target_pixels[x:x + block_width, y:y + block_height, 3].mean()
            color = Color(round(mean_r), round(mean_g), round(mean_b), round(mean_a))

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
    for block_size in np.arange(5, min(width, height) + 1, 5):
        moves = pixelate(target_image, initial_config, block_size)
        score = get_score(target_image, initial_config, moves)
        if score < best_score:
            best_moves = moves
            best_score = score

    return best_moves
