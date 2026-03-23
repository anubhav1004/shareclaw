#!/usr/bin/env python3
"""Download an official Open Problems dataset for the biology example."""

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EXAMPLE_DIR = Path(__file__).resolve().parent
for path in (ROOT, EXAMPLE_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from pipeline import download_file, resolve_dataset


def main():
    parser = argparse.ArgumentParser(description="Download an official Open Problems dataset.")
    parser.add_argument(
        "--dataset",
        default="zebrafish",
        choices=["zebrafish", "gtex_v9"],
        help="Named dataset shortcut.",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Destination .h5ad path. Defaults to examples/bio-label-projection/data/<dataset>.h5ad",
    )
    args = parser.parse_args()

    record = resolve_dataset(args.dataset)
    destination = (
        Path(args.output)
        if args.output
        else Path(__file__).resolve().parent / "data" / f"{args.dataset}.h5ad"
    )

    print(f"Downloading {args.dataset} from:")
    print(f"  {record['dataset_url']}")
    print(f"Destination:")
    print(f"  {destination}")
    download_file(record["dataset_url"], destination)
    print("Download complete.")


if __name__ == "__main__":
    main()
