import numpy as np
from core import Canvas, Color, ColorMove, Move, get_score
from PIL import Image
from typing import Any, Dict, List

def run(target_image: Image, initial_config: Dict[str, Any]) -> List[Move]:
    moves = []

    target_pixels = np.flip(np.array(target_image), 0)
    canvas = Canvas(initial_config)

    initial_score = get_score(target_image, initial_config, moves)

    for block in canvas.blocks.values():
        common_r = np.argmax(np.bincount(target_pixels[block.y:block.y + block.height, block.x:block.x + block.width, 0].flatten()))
        common_g = np.argmax(np.bincount(target_pixels[block.y:block.y + block.height, block.x:block.x + block.width, 1].flatten()))
        common_b = np.argmax(np.bincount(target_pixels[block.y:block.y + block.height, block.x:block.x + block.width, 2].flatten()))
        common_a = np.argmax(np.bincount(target_pixels[block.y:block.y + block.height, block.x:block.x + block.width, 3].flatten()))

        color = Color(common_r, common_g, common_b, common_a)
        move = ColorMove(block.id, color)

        new_score = get_score(target_image, initial_config, moves + [move])
        if new_score < initial_score:
            moves.append(move)

    return moves
