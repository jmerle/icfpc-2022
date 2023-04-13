import numpy as np
from enum import Enum
from dataclasses import dataclass, field
from pathlib import Path
from PIL import Image
from typing import Any, Dict, List

@dataclass
class Color:
    r: int
    g: int
    b: int
    a: int

    def __hash__(self: "Color") -> int:
        return hash((type(self),) + tuple(self.__dict__.values()))

class Orientation(Enum):
    VERTICAL = 0
    HORIZONTAL = 1

class Move:
    def to_isl(self: "Move") -> str:
        raise NotImplementedError()

@dataclass
class LineCutMove(Move):
    block: str
    orientation: Orientation
    line: int

    def to_isl(self: "LineCutMove") -> str:
        return f"cut [{self.block}] [{['x', 'y'][self.orientation.value]}] [{self.line}]"

@dataclass
class PointCutMove(Move):
    block: str
    x: int
    y: int

    def to_isl(self: "PointCutMove") -> str:
        return f"cut [{self.block}] [{self.x}, {self.y}]"

@dataclass
class ColorMove(Move):
    block: str
    color: Color

    def to_isl(self: "ColorMove") -> str:
        return f"color [{self.block}] [{self.color.r}, {self.color.g}, {self.color.b}, {self.color.a}]"

@dataclass
class SwapMove(Move):
    block1: str
    block2: str

    def to_isl(self: "SwapMove") -> str:
        return f"swap [{self.block1}] [{self.block2}]"

@dataclass
class MergeMove(Move):
    block1: str
    block2: str

    def to_isl(self: "MergeMove") -> str:
        return f"merge [{self.block1}] [{self.block2}]"

@dataclass
class Block:
    id: str
    x: int
    y: int
    width: int
    height: int
    size: int = field(init=False)

    def __post_init__(self: "Block") -> None:
        self.size = self.width * self.height

class Canvas:
    def __init__(self: "Canvas", initial_config: Dict[str, Any]) -> None:
        self.width = initial_config["width"]
        self.height = initial_config["height"]
        self.size = self.width * self.height

        self.pixels = np.full((self.height, self.width, 4), 255, dtype=np.uint8)

        self.blocks = {}
        for block in initial_config["blocks"]:
            new_block = Block(block["blockId"],
                              block["bottomLeft"][0], block["bottomLeft"][1],
                              block["topRight"][0] - block["bottomLeft"][0], block["topRight"][1] - block["bottomLeft"][1])
            self.add_block(new_block)
            self.apply_move(ColorMove(new_block.id, Color(*block["color"])))

        self.next_block_id = len(self.blocks)

    def apply_move(self: "Canvas", move: Move) -> int:
        if isinstance(move, LineCutMove):
            block = self.get_block_by_id(move.block)

            if move.orientation == Orientation.VERTICAL:
                if move.line <= block.x or move.line >= block.x + block.width:
                    raise ValueError(f"Cut coordinates are outside the block")

                self.add_block(Block(f"{block.id}.0", block.x, block.y, move.line - block.x, block.height))
                self.add_block(Block(f"{block.id}.1", move.line, block.y, block.width - (move.line - block.x), block.height))
            else:
                if move.line <= block.y or move.line >= block.y + block.height:
                    raise ValueError(f"Cut coordinates are outside the block")

                self.add_block(Block(f"{block.id}.0", block.x, block.y, block.width, move.line - block.y))
                self.add_block(Block(f"{block.id}.1", block.x, move.line, block.width, block.height - (move.line - block.y)))

            self.remove_block(block.id)

            return round(7 * self.size / block.size)
        elif isinstance(move, PointCutMove):
            block = self.get_block_by_id(move.block)

            if move.x <= block.x or move.x >= block.x + block.width or move.y <= block.y or move.y >= block.y + block.height:
                raise ValueError(f"Cut coordinates are outside the block")

            self.add_block(Block(f"{block.id}.0", block.x, block.y, move.x - block.x, move.y - block.y))
            self.add_block(Block(f"{block.id}.1", move.x, block.y, block.width - (move.x - block.x), move.y - block.y))
            self.add_block(Block(f"{block.id}.2", move.x, move.y, block.width - (move.x - block.x), block.height - (move.y - block.y)))
            self.add_block(Block(f"{block.id}.3", block.x, move.y, move.x - block.x, block.height - (move.y - block.y)))
            self.remove_block(block.id)

            return round(10 * self.size / block.size)
        elif isinstance(move, ColorMove):
            block = self.get_block_by_id(move.block)

            self.pixels[block.y:block.y + block.height, block.x:block.x + block.width, 0] = move.color.r
            self.pixels[block.y:block.y + block.height, block.x:block.x + block.width, 1] = move.color.g
            self.pixels[block.y:block.y + block.height, block.x:block.x + block.width, 2] = move.color.b
            self.pixels[block.y:block.y + block.height, block.x:block.x + block.width, 3] = move.color.a

            return round(5 * self.size / block.size)
        elif isinstance(move, SwapMove):
            block1 = self.get_block_by_id(move.block1)
            block2 = self.get_block_by_id(move.block2)

            if block1.width != block2.width or block1.height != block2.height:
                raise ValueError(f"Blocks have different shapes")

            self.pixels[block1.y:block1.y + block1.height, block1.x:block1.x + block1.width, :], \
            self.pixels[block2.y:block2.y + block2.height, block2.x:block2.x + block2.width, :] = \
            self.pixels[block2.y:block2.y + block2.height, block2.x:block2.x + block2.width, :], \
            self.pixels[block1.y:block1.y + block1.height, block1.x:block1.x + block1.width, :].copy()

            block1.x, block1.y = block2.x, block2.y

            return round(3 * self.size / block1.size)
        elif isinstance(move, MergeMove):
            block1 = self.get_block_by_id(move.block1)
            block2 = self.get_block_by_id(move.block2)

            if block1.x == block2.x and block1.width == block2.width and block1.y + block1.height == block2.y:
                self.add_block(Block(f"{self.next_block_id}", block1.x, block1.y, block1.width, block1.height + block2.height))
            elif block1.x == block2.x and block1.width == block2.width and block2.y + block2.height == block1.y:
                self.add_block(Block(f"{self.next_block_id}", block2.x, block2.y, block1.width, block1.height + block2.height))
            elif block1.y == block2.y and block1.height == block2.height and block1.x + block1.width == block2.x:
                self.add_block(Block(f"{self.next_block_id}", block1.x, block1.y, block1.width + block2.width, block1.height))
            elif block1.y == block2.y and block1.height == block2.height and block2.x + block2.width == block1.x:
                self.add_block(Block(f"{self.next_block_id}", block2.x, block2.y, block1.width + block2.width, block1.height))
            else:
                raise ValueError(f"Blocks are not adjoint, or their adjoint sides do not have the same length")

            self.remove_block(block1.id)
            self.remove_block(block2.id)
            self.next_block_id += 1

            return round(1 * self.size / max(block1.size, block2.size))
        else:
            raise NotImplementedError()

    def get_block_by_id(self: "Canvas", id: str) -> Block:
        if id not in self.blocks:
            raise ValueError(f"Block {id} does not exist")

        return self.blocks[id]

    def get_block_by_pixel(self: "Canvas", x: int, y: int) -> Block:
        if x < 0 or x >= self.width or y < 0 or y >= self.height:
            raise ValueError(f"Given coordinates are outside the canvas")

        for block in self.blocks.values():
            if block.x <= x < block.x + block.width and block.y <= y < block.y + block.height:
                return block

        raise RuntimeError("No block exists for the given coordinates, this is a bug")

    def add_block(self: "Canvas", block: Block) -> None:
        self.blocks[block.id] = block

    def remove_block(self: "Canvas", id: str) -> None:
        self.blocks.pop(id)

    def save_to_image(self: "Canvas", destination: Path) -> None:
        Image.fromarray(np.flip(self.pixels, 0)).save(destination)

class MoveError(Exception):
    def __init__(self: "MoveError", move: Move, index: int, message: str) -> None:
        super().__init__(f"{message} (move {index + 1}: {move.to_isl()})")

def get_score(target_image: Image, initial_config: Dict[str, Any], moves: List[Move]) -> int:
    canvas = Canvas(initial_config)

    total_cost = 0
    for i, move in enumerate(moves):
        try:
            total_cost += canvas.apply_move(move)
        except Exception as e:
            raise RuntimeError(f"Could not apply move {i + 1}: {move.to_isl()}") from e

    target_pixels = np.flip(np.array(target_image), 0)
    similarity = round(np.sqrt(((canvas.pixels.astype(np.int32) - target_pixels.astype(np.int32)) ** 2).sum(axis=2)).sum() * 0.005)

    return total_cost + similarity
