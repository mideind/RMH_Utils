#!/bin/bash

OUT_PATH="/data/datasets/text/is/rmh-2022/extracted/"

./extract_rmh.py --to_jsonl --ordering lookup --domain lookup --flatten_depth 0 --out_dir "$OUT_PATH" --in_path /data/datasets/text/is/rmh-2022/IGC-Adjud-22.10.TEI.zip --replace_name_placeholders
./extract_rmh.py --to_jsonl --ordering lookup --domain lookup --flatten_depth 0 --out_dir "$OUT_PATH" --in_path /data/datasets/text/is/rmh-2022/IGC-Books-22.10.TEI.zip
./extract_rmh.py --to_jsonl --ordering lookup --domain lookup --flatten_depth 0 --out_dir "$OUT_PATH" --in_path /data/datasets/text/is/rmh-2022/IGC-Journals-22.10.TEI.zip
./extract_rmh.py --to_jsonl --ordering lookup --domain lookup --flatten_depth 0 --out_dir "$OUT_PATH" --in_path /data/datasets/text/is/rmh-2022/IGC-Law-22.10.TEI.zip
./extract_rmh.py --to_jsonl --ordering lookup --domain lookup --flatten_depth 1 --out_dir "$OUT_PATH" --in_path /data/datasets/text/is/rmh-2022/IGC-News1-22.10.TEI.zip
./extract_rmh.py --to_jsonl --ordering lookup --domain lookup --flatten_depth 2 --out_dir "$OUT_PATH" --in_path /data/datasets/text/is/rmh-2022/IGC-News2-22.10.TEI.zip
./extract_rmh.py --to_jsonl --ordering lookup --domain lookup --flatten_depth 0 --out_dir "$OUT_PATH" --in_path /data/datasets/text/is/rmh-2022/IGC-Parla-22.10.TEI.zip
./extract_rmh.py --to_jsonl --ordering lookup --domain lookup --flatten_depth 2 --out_dir "$OUT_PATH" --in_path /data/datasets/text/is/rmh-2022/IGC-Social-22.10.TEI.zip
./extract_rmh.py --to_jsonl --ordering lookup --domain lookup --flatten_depth 0 --out_dir "$OUT_PATH" --in_path /data/datasets/text/is/rmh-2022/IGC-Wiki-22.10.TEI.zip
