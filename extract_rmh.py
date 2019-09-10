#!/usr/bin/env python3
# coding: utf-8

import zipfile
from pathlib import Path
import traceback
import rmhfile

# SCRIPT_DIR = Path(os.path.dirname(os.path.realpath("__file__")))
# OUTPUT_DIR = SCRIPT_DIR / "uncompress_data"
# os.makedirs(OUTPUT_DIR, exist_ok=True)

# p1 = Path("rmh1.zip")
# p2 = Path("rmh2.zip")
# p = Path("/home/haukur/Downloads/wordsim353.zip")

DEFAULT_EXPORT_DIR = Path("./extracted")
DEFAULT_OUTPUT_NAME = "output.tsv"
FLATTEN_DEPTH = 3
MAX_BUFFER_SIZE = 10 ** 6  # lines


def extract_all(in_path=None, out_path=None):
    base_out_path = out_path
    base_out_path.mkdir(exist_ok=True, parents=True)
    last_out_path = None

    buf = []
    with zipfile.ZipFile(str(in_path)) as archive:
        for item_name in archive.namelist():
            if not item_name:
                continue
            item_path = Path(item_name)

            if ".xml" not in item_path.suffixes:
                continue
            path_parents = list(reversed(item_path.parents))

            out_fname = DEFAULT_OUTPUT_NAME
            condensed_rel_path = path_parents[-1]
            if len(path_parents) > FLATTEN_DEPTH:
                condensed_rel_path = path_parents[FLATTEN_DEPTH].parent
                out_fname = Path(path_parents[FLATTEN_DEPTH].name).with_suffix(".tsv")

            out_path_parent = base_out_path / condensed_rel_path
            out_path_parent.mkdir(exist_ok=True, parents=True)
            out_path = out_path_parent / out_fname

            new_data = []
            try:
                with archive.open(str(item_path)) as item:
                    rmhf = rmhfile.RMHFile.fromstring(item.read())
                    new_data = [fields for fields in rmhf.indexed_sentence_text()]
            except KeyboardInterrupt:
                return
            except Exception:
                new_data = []
                print("Skipping:", item_name)
                traceback.print_exc()

            try:
                if out_path == last_out_path and len(buf) < MAX_BUFFER_SIZE:
                    buf.extend(new_data)
                elif len(buf) > 0:
                    with out_path.open(mode="a") as out_file:
                        for fields in buf:
                            out_file.write("\t".join(fields))
                            out_file.write("\n")
                        buf = []
                    buf.extend(new_data)
            except KeyboardInterrupt:
                return
            except Exception:
                new_data = []
                print("Could not write to file", out_path)
                traceback.print_exc()

            last_out_path = out_path


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser("Extract RMH.zip file to tsv format")

    def file_type_guard(path):
        path = Path(path)
        if path.is_file():
            return path
        raise argparse.ArgumentError(
            "Expected path to a file but got '{0}'".format(path)
        )

    parser.add_argument(
        "-i",
        "--in_path",
        dest="in_path",
        type=file_type_guard,
        required=True,
        default="default",
        help="Path to RMH zip file",
    )
    parser.add_argument(
        "-o",
        "--out_path",
        dest="out_path",
        type=Path,
        required=False,
        default=DEFAULT_EXPORT_DIR,
        help="Path to output file",
    )

    args = parser.parse_args()
    args.out_path.mkdir(exist_ok=True, parents=True)

    extract_all(in_path=args.in_path, out_path=args.out_path)
