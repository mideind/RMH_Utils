#!/usr/bin/env python3
"""
    Reynir: Natural language processing for Icelandic

     RMH Converter

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

     Extraction and conversion utility for the RMH corpus
"""


import zipfile
from pathlib import Path
import traceback
import rmhfile

try:
    from icecream import ic
    ic.configureOutput(includeContext=True)
except ImportError:  # Graceful fallback if IceCream isn't installed.
    ic = lambda *a: None if not a else (a[0] if len(a) == 1 else a)  # noqa

from tqdm import tqdm

DEFAULT_EXPORT_DIR = Path("./extracted")
DEFAULT_OUTPUT_NAME = "output.tsv"
FLATTEN_DEPTH = 3
MAX_BUFFER_SIZE = 10 ** 6  # lines


def extract_all(in_path=None, out_path=None, include_sports=True, include_meta=True):
    base_out_path = out_path
    base_out_path.mkdir(exist_ok=True, parents=True)
    last_out_path = None

    buf = []
    ic()
    with zipfile.ZipFile(str(in_path)) as archive:
        for item_name in tqdm(archive.namelist()):
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
                    if not item:
                        import pdb; pdb.set_trace()
                        ic()
                    text = item.read()
                    if not text:
                        import pdb; pdb.set_trace()
                        ic()
                    try:
                        rmhf = rmhfile.RMHFile.fromstring(text)
                    except:
                        print("File {} broken, skipping".format(item_path))
                        continue
                    if not rmhf:
                        continue
                    if not include_sports and rmhf.is_sports:
                        continue
                    if rmhf.ref is None:
                        ref = ""
                    else:
                        ref = rmhf.ref
		    meta_data = []
                    if include_meta:
                        meta_data = [rmhf.title, rmhf.author, ref, rmhf.date]
                    new_data = [meta_data + list(fields) for fields in rmhf.indexed_sentence_text()]
            except KeyboardInterrupt:
                return
            # except Exception:
            #     new_data = []
            #     print("Skipping:", item_name)
            #     traceback.print_exc()
            #     continue

            try:
                if last_out_path is None:
                    last_out_path = out_path
                if out_path == last_out_path and len(buf) <= MAX_BUFFER_SIZE:
                    buf.extend(new_data)
                elif out_path == last_out_path and len(buf) > MAX_BUFFER_SIZE:
                    with last_out_path.open(mode="a") as out_file:
                        buf.extend(new_data)
                        for fields in buf:
                            out_file.write("\t".join(fields))
                            out_file.write("\n")
                        buf = []
                elif buf:
                    with last_out_path.open(mode="a") as out_file:
                        for fields in buf:
                            out_file.write("\t".join(fields))
                            out_file.write("\n")
                        buf = []
                    buf.extend(new_data)
                else:
                    buf.extend(new_data)
            except KeyboardInterrupt:
                return
            except Exception:
                new_data = []
                print("Could not write to file", out_path)
                traceback.print_exc()

            last_out_path = out_path
        if buf:
            with last_out_path.open(mode="a") as out_file:
                for fields in buf:
                    out_file.write("\t".join(fields))
                    out_file.write("\n")
                buf = []


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser("Extract RMH.zip file to tsv format")

    def file_type_guard(path):
        path = Path(path)
        if path.is_file():
            return path
        raise ValueError(
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
    parser.add_argument(
        "--no-sports",
        dest="sports",
        action="store_true",
        help="Ignore sports",
    )
    parser.add_argument(
        "--no-meta",
        desta="no_meta",
        action="store_true"
        help="Don't print file name, author, url and date in tsv"
    )

    args = parser.parse_args()
    args.out_path.mkdir(exist_ok=True, parents=True)

    extract_all(in_path=args.in_path, out_path=args.out_path, include_sports=not args.sportsi, include_meta=not args.no_meta)
