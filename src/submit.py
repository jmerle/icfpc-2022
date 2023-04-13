import argparse
import os
import requests
import time
from io import StringIO
from pathlib import Path

def main() -> None:
    parser = argparse.ArgumentParser(description="Submit a painter's results.")
    parser.add_argument("painter", type=str, help="the painter to submit the results of")
    parser.add_argument("--image", type=int, help="the image to submit the results of (defaults to all images)")

    args = parser.parse_args()

    output_directory = Path(__file__).parent.parent / "results" / "output" / args.painter
    if not output_directory.is_dir():
        raise RuntimeError(f"{output_directory} does not exist")

    submit_files = []
    if args.image is not None:
        submit_files = [output_directory / f"{args.image}.isl"]
        if not submit_files[0].is_file():
            raise RuntimeError(f"{submit_files[0]} does not exist")
    else:
        submit_files = sorted(output_directory.glob("*.isl"), key=lambda file: int(file.stem))

    for file in submit_files:
        content = file.read_text(encoding="utf-8")

        response = requests.post(f"https://robovinci.xyz/api/submissions/{file.stem}/create",
                                 headers={"Authorization": f"Bearer {os.environ['ICFPC_2022_API_KEY']}"},
                                 files={"file": ("submission.isl", StringIO(content))})
        response.raise_for_status()

        print(f"Successfully submitted {file.stem}")

    time.sleep(1)

    response = requests.get(f"https://robovinci.xyz/api/results/user",
                            headers={"Authorization": f"Bearer {os.environ['ICFPC_2022_API_KEY']}"})
    response.raise_for_status()

    print(f"Total cost: {response.json()['total_cost']:,.0f}")
    print("Dashboard: https://robovinci.xyz/dashboard")
    print("Scoreboard: https://robovinci.xyz/scoreboard")

if __name__ == "__main__":
    main()
