import numpy as np
from core import Canvas, Color, ColorMove, Move
from PIL import Image
from typing import Any, Dict, List

def run(target_image: Image, initial_config: Dict[str, Any]) -> List[Move]:
    moves = []

    target_pixels = np.flip(np.array(target_image), 0)
    canvas = Canvas(initial_config)

    for block in canvas.blocks.values():
        mean_r = target_pixels[block.y:block.y + block.height, block.x:block.x + block.width, 0].mean()
        mean_g = target_pixels[block.y:block.y + block.height, block.x:block.x + block.width, 1].mean()
        mean_b = target_pixels[block.y:block.y + block.height, block.x:block.x + block.width, 2].mean()
        mean_a = target_pixels[block.y:block.y + block.height, block.x:block.x + block.width, 3].mean()

        color = Color(round(mean_r), round(mean_g), round(mean_b), round(mean_a))
        moves.append(ColorMove(block.id, color))

    return moves
