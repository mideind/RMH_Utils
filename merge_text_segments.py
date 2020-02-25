"""
    Reynir: Natural language processing for Icelandic

    Segmet merger

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

      Utility script that merges adjacent text segments until they are close to a
      certain length. If a sentence is too long, the characters that exceed the max_length
      will be removed.
"""

import sys
from collections import namedtuple

MAX_CHARS_IN_BATCH = 400
MAX_LINES_MERGED_IN_BATCH = 6
CorpusLine = namedtuple("CorpusLine", ["file_id", "par_idx", "sent_idx", "text"])


def parse_line(line, max_len):
    segment_id, *text = line.split("\t", 2)
    if text:
        text = text[0]
    else:
        text = ""
    if max_len is not None and len(text) > max_len:
        text = text[:max_len]
    file_id, par_idx, sent_idx = segment_id.split(".")
    corpline = CorpusLine(file_id, par_idx, sent_idx, text)
    return corpline


def merge_lines(batch):
    if len(batch) == 0:
        return None
    line = batch[0]
    segments = [line.text for line in batch]
    sent_idx = line.sent_idx
    if len(batch) > 1:
        sent_idx = "-".join([line.sent_idx, batch[-1].sent_idx])
    merged = "{file_id}.{par}.{sent}\t{text}".format(
        file_id=line.file_id, par=line.par_idx, sent=sent_idx, text=" ".join(segments)
    )
    return merged


def line_merger(lines, max_len=MAX_CHARS_IN_BATCH, max_merge=MAX_LINES_MERGED_IN_BATCH):
    batch = []
    total = 0
    file_id = None
    for line in lines:
        line = parse_line(line.strip(), max_len)

        if len(batch) == 0:
            par_idx = line.par_idx
            file_id = line.file_id

        is_contiguous = (
            True
            if len(batch) < 2
            else (int(line.sent_idx) + 1 == int(batch[-1].sent_idx))
        )
        is_same_paragraph = (file_id, par_idx) == (line.file_id, line.par_idx)
        if not is_same_paragraph or not is_contiguous:
            # new paragraph or new file
            yield merge_lines(batch)
            batch, total = [], 0
            par_idx = line.par_idx
            file_id = line.file_id

        next_total = total + len(line.text)
        if (next_total > max_len and len(batch) != 0) or len(
            batch
        ) >= MAX_LINES_MERGED_IN_BATCH:
            # buffer is full
            yield merge_lines(batch)
            batch, total = [line], len(line.text)
        else:
            total += len(line.text)
            batch.append(line)
    if batch:
        yield merge_lines(batch)


def path_filetype(path_string):
    from pathlib import Path

    path = Path(path_string)
    return path if path.exists() else None


def main():
    import argparse

    try:
        import argcomplete
    except ImportError as e:
        pass
    parser = argparse.ArgumentParser("Description")

    parser.add_argument(
        "-i",
        "--input",
        dest="in_file",
        required=False,
        type=path_filetype,
        default="-",
        help="Path to the tsv file that will be processed, defaults to stdin",
    )
    parser.add_argument(
        "-o",
        "--output",
        dest="out_file",
        required=False,
        type=str,
        default=sys.stdout,
        help="Path to the output file, defaults to stdout",
    )
    parser.add_argument(
        "-l",
        "--max-lines",
        dest="max_lines",
        required=False,
        type=int,
        default=MAX_LINES_MERGED_IN_BATCH,
        help="Maximum number of lines that can be merged together",
    )
    parser.add_argument(
        "-c",
        "--max-chars",
        dest="max_chars",
        required=False,
        type=int,
        default=MAX_CHARS_IN_BATCH,
        help="Maximum number of chars after merging",
    )

    args = parser.parse_args()

    with open(str(args.out_file), mode="w") as out_handle:
        with open(str(args.in_file), mode="r") as in_handle:
            for output_line in line_merger(
                in_handle, max_len=args.max_chars, max_merge=args.max_lines
            ):
                print(output_line, file=out_handle)


if __name__ == "__main__":
    main()
