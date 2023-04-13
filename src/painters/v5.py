import numpy as np
from copy import deepcopy
from core import Canvas, Color, ColorMove, PointCutMove, get_score, Move
from PIL import Image
from typing import Any, Dict, List

def run(target_image: Image, initial_config: Dict[str, Any]) -> List[Move]:
    target_pixels = np.flip(np.array(target_image), 0)

    moves = []
    canvas = Canvas(initial_config)

    best_score = get_score(target_image, initial_config, moves)

    block_queue = list(canvas.blocks.values())
    while len(block_queue) > 0:
        block = block_queue.pop(0)

        current_moves = moves
        current_canvas = canvas
        current_score = best_score
        current_new_blocks = []

        for split_x in range(block.x + 10, block.x + block.width, 10):
            for split_y in range(block.y + 10, block.y + block.height, 10):
                new_moves = moves.copy()
                new_canvas = deepcopy(canvas)

                new_moves.append(PointCutMove(block.id, split_x, split_y))
                new_canvas.apply_move(new_moves[-1])

                new_blocks = [new_canvas.get_block_by_id(f"{block.id}.{sub_id}") for sub_id in range(4)]
                for new_block in new_blocks:
                    common_r = np.argmax(np.bincount(target_pixels[new_block.y:new_block.y + new_block.height, new_block.x:new_block.x + new_block.width, 0].flatten()))
                    common_g = np.argmax(np.bincount(target_pixels[new_block.y:new_block.y + new_block.height, new_block.x:new_block.x + new_block.width, 1].flatten()))
                    common_b = np.argmax(np.bincount(target_pixels[new_block.y:new_block.y + new_block.height, new_block.x:new_block.x + new_block.width, 2].flatten()))
                    common_a = np.argmax(np.bincount(target_pixels[new_block.y:new_block.y + new_block.height, new_block.x:new_block.x + new_block.width, 3].flatten()))
                    color = Color(common_r, common_g, common_b, common_a)

                    new_moves.append(ColorMove(new_block.id, color))
                    new_canvas.apply_move(new_moves[-1])

                new_score = get_score(target_image, initial_config, new_moves)
                if new_score <= current_score:
                    current_moves = new_moves
                    current_canvas = new_canvas
                    current_new_blocks = new_blocks
                    current_score = new_score

        if current_score <= best_score:
            moves = current_moves
            canvas = current_canvas
            block_queue.extend(current_new_blocks)
            best_score = current_score

    return moves
