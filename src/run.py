import argparse
import importlib
import json
from core import Canvas, get_score
from pathlib import Path
from PIL import Image

def update_overview() -> None:
    scores_by_painter = {}
    outputs_root = Path(__file__).parent.parent / "results" / "output"

    for directory in outputs_root.iterdir():
        scores_by_image = {}

        for file in directory.iterdir():
            if file.name.endswith(".txt"):
                scores_by_image[file.stem] = int(file.read_text(encoding="utf-8"))

        scores_by_painter[directory.name] = scores_by_image

    overview_template_file = Path(__file__).parent.parent / "results" / "overview.tmpl.html"
    overview_file = Path(__file__).parent.parent / "results" / "overview.html"

    overview_template = overview_template_file.read_text(encoding="utf-8")
    overview = overview_template.replace("/* scores_by_painter */{}", json.dumps(scores_by_painter))

    with overview_file.open("w+", encoding="utf-8") as file:
        file.write(overview)

    print(f"Overview: file://{overview_file}")

def main() -> None:
    parser = argparse.ArgumentParser(description="Run a painter.")
    parser.add_argument("painter", type=str, help="the painter to run")
    parser.add_argument("--image", type=int, help="the image to run on (defaults to all images)")

    args = parser.parse_args()

    painter = importlib.import_module(f"painters.{args.painter}")
    output_directory = Path(__file__).parent.parent / "results" / "output" / args.painter
    output_directory.mkdir(parents=True, exist_ok=True)

    total_score = 0

    if args.image is not None:
        image_files = [Path(__file__).parent.parent / "results" / "input" / f"{args.image}.png"]
        if not image_files[0].is_file():
            raise RuntimeError(f"{image_files[0]} does not exist")
    else:
        image_files = sorted((Path(__file__).parent.parent / "results" / "input").glob("*.png"), key=lambda file: int(file.stem))

    for image_file in image_files:
        image = Image.open(image_file)

        initial_config = json.loads((image_file.parent / f"{image_file.stem}.json").read_text(encoding="utf-8"))

        moves = painter.run(image, initial_config)

        score = get_score(image, initial_config, moves)
        total_score += score

        with (output_directory / f"{image_file.stem}.isl").open("w+", encoding="utf-8") as file:
            file.write("\n".join(move.to_isl() for move in moves) + "\n")

        canvas = Canvas(initial_config)
        for move in moves:
            canvas.apply_move(move)
        canvas.save_to_image(output_directory / f"{image_file.stem}.png")

        with (output_directory / f"{image_file.stem}.txt").open("w+", encoding="utf-8") as file:
            file.write(str(int(score)))

        print(f"{image_file.stem}: {score:,.0f}")

    if len(image_files) > 1:
        print(f"Total score: {total_score:,.0f}")

    update_overview()

if __name__ == "__main__":
    main()
