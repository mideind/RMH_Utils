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


import logging
import zipfile
from collections import defaultdict
from multiprocessing import Pool
from pathlib import Path
from typing import Dict, List

from tqdm import tqdm

import rmhfile
from combine_text import split_sentences

DEFAULT_EXPORT_DIR = Path("./extracted_rmh")
DEFAULT_FLATTEN_DEPTH = 0


def archive_path_to_outpath(
    archive_paths: List[Path],
    out_path: Path,
    flatten_depth: int,
    accepted_suffixes: List[str],
    output_file_suffix=".txt",
) -> Dict[Path, Path]:
    """Traverse the namelist and assign each element to an output file.
    If the depth of an element to more than the flatten_depth, it is aggregated to parent's output file."""
    archive_paths = list(
        filter(lambda x: accepted_suffixes == x.suffixes, archive_paths)
    )
    potential_namelist = [
        list(reversed(x.parents))[1:] + [x] for x in archive_paths
    ]  # Skip the "." and add the file itself
    output_names = [
        out_path / x[min(flatten_depth, len(x) - 1)] for x in potential_namelist
    ]
    output_names_with_suffix = [x.with_suffix(output_file_suffix) for x in output_names]
    namelist_mapping = {
        archive_paths[i]: output_names_with_suffix[i] for i in range(len(archive_paths))
    }
    return namelist_mapping


def extract_rmh_to_txt(
    rmhf: rmhfile.RMHFile,
    sentence_separator="\n",
    document_separator="\n",
    paragraph_separator="\n",
) -> str:
    """Extract a single RMHFile to a text file"""
    return (
        paragraph_separator.join(  # Join paragraphs
            [
                sentence_separator.join(  # Join sentences into paragraphs again.
                    map(
                        lambda x: x
                        if x[0] != " "
                        else x[
                            1:
                        ],  # Remove the space at the beginning of consecutive sentences
                        split_sentences(paragraph),
                    )
                )
                for paragraph in rmhf.paragraphs()
            ]
        )
        + document_separator  # Add a document separator
    )


def extract_all(
    zip_file_path: Path,
    out_path: Path,
    flatten_depth: int,
    accepted_suffixes: List[str],
    processes: int,
    chunksize: int,
) -> None:
    # Please note that the zipfile module is not thread-safe even though it should be: https://bugs.python.org/issue42369
    with zipfile.ZipFile(str(zip_file_path)) as archive:
        archive_paths = [Path(x) for x in archive.namelist()]
        namelist_to_outpath_mapping = archive_path_to_outpath(
            archive_paths, out_path, flatten_depth, accepted_suffixes
        )
        outpath_to_namelist = defaultdict(list)
        for archive_path, outpath in namelist_to_outpath_mapping.items():
            outpath_to_namelist[outpath].append(archive_path)

        total_archive_files = len(namelist_to_outpath_mapping)
        p_bar = tqdm(
            desc=f"Extracting {zip_file_path}", total=total_archive_files, unit="files"
        )
        reading_batch_size = (
            processes * chunksize * 4
        )  # Reading the file on the main thread is blocking, so we try to read in batches
        with Pool(processes=processes) as pool:
            for out_path, names in outpath_to_namelist.items():
                out_path.parent.mkdir(parents=True, exist_ok=True)
                with open(out_path, "w", encoding="utf-8") as f:
                    for current_idx in range(0, len(names), reading_batch_size):
                        batch = names[current_idx : current_idx + reading_batch_size]
                        rmh_files = []
                        for archive_path in batch:
                            # We read the zipfile on the main thread.
                            with archive.open(str(archive_path)) as item:
                                text = item.read().decode("utf-8")
                                rmh_files.append(rmhfile.RMHFile(text, archive_path))
                        # Parse the xml
                        for text in pool.map(
                            extract_rmh_to_txt, rmh_files, chunksize=chunksize
                        ):
                            f.write(text)
                            p_bar.update()
                        rmh_files.clear()
        p_bar.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser("Extract RMH.zip file to txt format")

    def file_type_guard(path) -> Path:
        path = Path(path)
        if path.is_file():
            return path
        raise ValueError("Expected path to a file but got '{0}'".format(path))

    parser.add_argument(
        "-i",
        "--in_path",
        dest="in_path",
        type=file_type_guard,
        required=True,
        help="Path to RMH zip file",
    )
    parser.add_argument(
        "-o",
        "--out_path",
        dest="out_path",
        type=Path,
        required=False,
        default=DEFAULT_EXPORT_DIR,
        help="Path to base output directory",
    )
    parser.add_argument(
        "--flatten-depth",
        dest="flatten_depth",
        type=int,
        default=DEFAULT_FLATTEN_DEPTH,
        help="The RMH file-tree structure is deep. \
Instead of exporting all the files, we combine files which are deeper than the 'flatten_depth' into a single file. \
0 will map each top-level directory in the zipfile to a single file. 1 will create a single directory per top-level directory in the zipfile, etc.",
    )
    parser.add_argument(
        "--processes",
        type=int,
        default=20,
        help="The number of processes to use when parsing XML for each output file.",
    )
    parser.add_argument(
        "--chunksize",
        type=int,
        default=10,
        help="The number of XML files to send to each process.",
    )
    parser.add_argument(
        "--no-meta",
        dest="no_meta",
        action="store_true",
        help="Don't print file name, author, url and date in tsv",
    )

    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)

    extract_all(
        zip_file_path=args.in_path,
        out_path=args.out_path,
        flatten_depth=args.flatten_depth,
        # TODO: Add support for ana.xml
        accepted_suffixes=[".xml"],
        processes=args.processes,
        chunksize=args.chunksize,
    )
