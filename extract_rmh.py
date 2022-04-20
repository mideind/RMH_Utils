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


import json
import logging
import uuid
import zipfile
from collections import defaultdict
from functools import partial
from multiprocessing import Pool
from pathlib import Path
from typing import Dict, List, Optional

from tokenizer import split_into_sentences
from tqdm import tqdm

import rmhfile

DEFAULT_EXPORT_DIR = Path("./extracted_rmh")
DEFAULT_FLATTEN_DEPTH = 0


def archive_file_to_output_file(
    archive_paths: List[Path],
    out_dir: Path,
    flatten_depth: int,
    accepted_suffixes: List[str],
    output_file_suffix=".txt",
) -> Dict[Path, Path]:
    """Traverse the archive's files and assign each file to an output file.
    If the nested depth of a file to more than the flatten_depth, it is aggregated to parent's output file."""
    archive_paths = list(filter(lambda x: accepted_suffixes == x.suffixes, archive_paths))
    potential_namelist = [
        list(reversed(x.parents))[1:] + [x] for x in archive_paths
    ]  # Skip the "." and add the file itself
    output_names = [out_dir / x[min(flatten_depth, len(x) - 1)] for x in potential_namelist]
    output_names_with_suffix = [x.with_suffix(output_file_suffix) for x in output_names]
    namelist_mapping = {archive_paths[i]: output_names_with_suffix[i] for i in range(len(archive_paths))}
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
                        lambda x: x.lstrip(" "),  # Remove the space at the beginning of consecutive sentences
                        split_into_sentences(paragraph, original=True),
                    )
                )
                + sentence_separator
                for paragraph in rmhf.paragraphs()
            ]
        )
        + paragraph_separator
        + document_separator  # Add a document separator
    )


def extract_rmh_to_json_string(rmhf: rmhfile.RMHFile, domains: Optional[List[str]]) -> str:
    """Extract a single RMHFile to a json string"""
    return (
        json.dumps(
            {
                "uuid": str(uuid.uuid4()),
                "lang": "is",
                "document": [
                    list(
                        map(
                            lambda sentence: sentence.lstrip(" "),  # Remove the space at the beginning of consecutive sentences
                            split_into_sentences(paragraph, original=True),
                        )
                    )
                    for paragraph in rmhf.paragraphs()
                ],
                "domains": domains,
                "title": rmhf.title,
            },
            ensure_ascii=False,
        )
        + "\n"
    )


def extract_all(
    zip_file_path: Path,
    output_file: Path,
    flatten_depth: int,
    accepted_suffixes: List[str],
    processes: int,
    chunksize: int,
    to_jsonl: bool,
    domains: Optional[List[str]],
) -> None:
    """Extract all files from a zip file to a files."""
    # Please note that the zipfile module is not thread-safe even though it should be: https://bugs.python.org/issue42369
    output_file_suffix = ".txt"
    parsing_function = extract_rmh_to_txt
    if to_jsonl:
        output_file_suffix = ".jsonl"
        parsing_function = partial(extract_rmh_to_json_string, domains=domains)

    with zipfile.ZipFile(str(zip_file_path)) as archive:
        archive_paths = [Path(x) for x in archive.namelist()]
        archive_file_to_output_file_map = archive_file_to_output_file(
            archive_paths,
            output_file,
            flatten_depth,
            accepted_suffixes,
            output_file_suffix=output_file_suffix,
        )
        output_file_to_archive_files_map = defaultdict(list)
        for archive_file, output_file in archive_file_to_output_file_map.items():
            output_file_to_archive_files_map[output_file].append(archive_file)

        total_archive_files = len(archive_file_to_output_file_map)
        p_bar = tqdm(desc=f"Extracting {zip_file_path}", total=total_archive_files, unit="files")
        reading_batch_size = (
            processes * chunksize * 4
        )  # Reading the file on the main thread is blocking, so we try to read in batches
        with Pool(processes=processes) as pool:
            for output_file, archive_files in output_file_to_archive_files_map.items():
                output_file.parent.mkdir(parents=True, exist_ok=True)
                with open(output_file, "w", encoding="utf-8") as f:
                    for current_idx in range(0, len(archive_files), reading_batch_size):
                        batch = archive_files[current_idx : current_idx + reading_batch_size]
                        rmh_files = []
                        for archive_file in batch:
                            # We read the zipfile on the main thread.
                            with archive.open(str(archive_file)) as item:
                                text = item.read().decode("utf-8")
                                rmh_files.append(rmhfile.RMHFile(text, archive_file))
                        # Parse the xml
                        for text in pool.map(parsing_function, rmh_files, chunksize=chunksize):
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
        "--out_dir",
        dest="out_dir",
        type=Path,
        required=False,
        default=DEFAULT_EXPORT_DIR,
        help="Path to base output directory",
    )
    parser.add_argument(
        "--flatten_depth",
        dest="flatten_depth",
        type=int,
        default=DEFAULT_FLATTEN_DEPTH,
        help="The RMH contains deeply nested folder. "
             "Instead of exporting all the files, we combine files which are within folders deeper than the 'flatten_depth' into a single file. "
             "0 will map each top-level directory in the zipfile file. "
             "1 will preserve the top-level directory in the zipfile, etc.",
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
        "--to_jsonl",
        action="store_true",
        default=False,
        help="If true, the output files will be in jsonl format. Otherwise, they will be in txt format.",
    )
    parser.add_argument(
        "--domains",
        type=str,
        nargs="+",
        default=None,
        help="When using jsonl format, the extracted files will be given these domains. "
             "Usage: --domains domain1 domain2 domain3",
    )

    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)

    extract_all(
        zip_file_path=args.in_path,
        output_file=args.out_dir,
        flatten_depth=args.flatten_depth,
        # TODO: Add support for ana.xml
        accepted_suffixes=[".xml"],
        processes=args.processes,
        chunksize=args.chunksize,
        to_jsonl=args.to_jsonl,
        domains=args.domains,
    )
