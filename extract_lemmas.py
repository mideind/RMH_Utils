#!/usr/bin/env python
"""
    Reynir: Natural language processing for Icelandic

     RMH lemma extractor

    Copyright (C) 2020 Miðeind ehf.

       This program is free software: you can redistribute it and/or modify
       it under the terms of the GNU General Public License as published by
       the Free Software Foundation, either version 3 of the License, or
       (at your option) any later version.
       This program is distributed in the hope that it will be useful,
       but WITHOUT ANY WARRANTY; without even the implied warranty of
       MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
       GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see http://www.gnu.org/licenses/.

     Extract parallel sentences with normal text and lemmatized text.
"""


import rmhfile
import os
import sys
import multiprocessing as mp
from pathlib import Path


def extract_single_file(input_path, output_dir, out_stem):
    rmhf = rmhfile.RMHFile(input_path)

    with open(output_dir/(out_stem+".is_IS"), "w") as f_is, \
         open(output_dir/(out_stem+".is_LEM"), "w") as f_lem:
        for s in rmhf.sentences:
            is_buf = []
            lem_buf = []
            for t in s.tokens:
                is_buf.append(t.text)
                lem_buf.append(t.lemma)

            f_is.write(" ".join(is_buf) + "\n")
            f_lem.write(" ".join(lem_buf) + "\n")


def process_queue(q, iolock):
    while True:
        args = q.get()
        if args is None:
            break
        try:
            extract_single_file(*args)
        except Exception as e:
            with iolock:
                print(f"Skipping problematic file: {Path(root)/relpath/fn}")


def find_files(input_path):
    for d, _, files in os.walk(input_path):
        for f in files:
            if f.endswith(".xml"):
                yield (input_path, os.path.relpath(d, input_path), f)


def extract_lemmas(input_path, output_path):
    q = mp.Queue(maxsize=16)
    iolock = mp.Lock()
    p = mp.Pool(16, initializer=process_queue, initargs=(q, iolock))
    for root, relpath, fn in find_files(input_path):
        out_dir = Path(output_path)/relpath
        out_dir.mkdir(exist_ok=True, parents=True)

        q.put((Path(root)/relpath/fn, out_dir, Path(fn).stem))

    """ non-mp version
    for root, relpath, fn in find_files(input_path):
        out_dir = Path(output_path)/relpath
        out_dir.mkdir(exist_ok=True, parents=True)
        try:
            extract_single_file(Path(root)/relpath/fn, out_dir, Path(fn).stem)
        except Exception as e:
            print(f"Skipping problematic file: {Path(root)/relpath/fn}")
    """


def check_and_make_paths(input_path, output_path):
    """ Check that inputs and outputs are reasonable and create output directory if needed """

    if not input_path.is_dir():
        raise Exception(f"Input path is not a directory: {input_path}")

    if output_path.exists() and not output_path.is_dir():
        raise Exception(f"Output path already exists and is not a directory: {output_path}")

    if output_path.is_dir():
        if any(os.scandir(output_path)):
            raise Exception(f"Output directory is not empty: {output_path}")
    
    output_path.mkdir(exist_ok=True, parents=True)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Extract parallel normal and lemmatized text from RMH xml files")

    parser.add_argument(
        "-i",
        "--input-path",
        type=Path,
        required=True,
        help="Path to directory with .xml files",
    )

    parser.add_argument(
        "-o",
        "--output-path",
        type=Path,
        required=True,
        help="Path to output directory",
    )

    args = parser.parse_args()

    try:
        check_and_make_paths(args.input_path, args.output_path)
    except Exception as e:
        print(e)
        sys.exit(1)

    extract_lemmas(args.input_path, args.output_path)
