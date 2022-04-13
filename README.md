# RMH Utils
A collection of scripts to help with extracting data from Risamálheild (RMH) / Icelandic Gigaword Corpus (IGC).

## Extracting paragraphs
To extract "raw text" from the IGC, you can use the following command:
```
./extract_rmh.py -i /path_to/IGC-Adjud-21.05.zip --flatten-depth 0  # extract to a single txt file
```
This will extract all paragraphs from the unannotated IGC.
Each paragraph is split into sentences using [`tokenizer`](https://github.com/mideind/Tokenizer).
- Sentences are separated with a newline.
- Paragraphs are separated with an additional newline, i.e. there is an empty line between paragraphs.
- Documents are separated with an additional newline, i.e. there are two empty line between documents.

Since the zip-files contains a lot of files, it is recommended to use the `--flatten_depth` option to combine multiple zip files in the archive to a fewer text file.
This option is best adjusted per zip-file.

Opinionated values for `--flatten_depth` are:
```
./extract_rmh.py -i /data/datasets/text/is/rmh-2021/IGC-Adjud-21.05.zip --flatten_depth 0 # single file: IGC-Adjud-21.05.txt
./extract_rmh.py -i /data/datasets/text/is/rmh-2021/IGC-Books-21.10.zip --flatten_depth 0 # single file: IGC-Books-21.10.txt
./extract_rmh.py -i /data/datasets/text/is/rmh-2021/IGC-Journals-21.12.zip --flatten_depth 0   # single file: IGC-Journals-21.12.txt
./extract_rmh.py -i /data/datasets/text/is/rmh-2021/IGC-Laws-21.05.zip --flatten_depth 0 # single file: IGC-Laws-21.05.txt
./extract_rmh.py -i /data/datasets/text/is/rmh-2021/IGC-News1-21.05.zip --flatten_depth 1 # single file: CC_BY/IGC-News1-21.05.txt
./extract_rmh.py -i /data/datasets/text/is/rmh-2021/IGC-News2-21.05.zip --flatten_depth 2 # multiple files under MIM/IGC-News2-21.05.TEI/
./extract_rmh.py -i /data/datasets/text/is/rmh-2021/IGC-Parla-21.12.zip --flatten_depth 0 # single file: IGC-Parla-21.12.txt
./extract_rmh.py -i /data/datasets/text/is/rmh-2021/IGC-Social-21.10.zip  --flatten_depth 2 # multiple files under TEI/IGC-Social-21.10.TEI/
```

For other options see `./extract_rmh.py --help`.

