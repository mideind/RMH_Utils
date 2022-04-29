# RMH Utils
A collection of scripts to help with extracting data from Risamálheild (RMH) / Icelandic Gigaword Corpus (IGC).

Supports version 21.05 of the IGC.

## Extracting paragraphs
To extract "raw text" from the IGC, you can use the following command:
```
./extract_rmh.py -i /path_to/IGC-Adjud-21.05.zip --flatten-depth 0  # extract to a single txt file
```
This will extract all paragraphs from the unannotated IGC.
Each paragraph is split into sentences using [`tokenizer`](https://github.com/mideind/Tokenizer).
- Sentences are separated with a newline.
- Paragraphs are separated with an additional newline, i.e. there is an empty line between paragraphs.
- Documents are separated with an additional newline, i.e. there are two empty lines between documents.

Since the zip-files contains a lot of deeply-nested folders, it is recommended to use the `--flatten_depth` option to ignore these nested folders by combining files from nested folder which depth exceeds `--flatten_depth` into a single output file.
This option controls how deep the nested structure is preserved in the output and is best adjusted per zip-file.

Suggested values for `--flatten_depth` are:
```
./extract_rmh.py -i /path/to/rmh-2021/IGC-Adjud-21.05.zip --flatten_depth 0     # each top level folder is combined into a single file, results in a single file: IGC-Adjud-21.05.txt
./extract_rmh.py -i /path/to/rmh-2021/IGC-Books-21.10.zip --flatten_depth 0     # each top level folder is combined into a single file, results in a single file: IGC-Books-21.10.txt
./extract_rmh.py -i /path/to/rmh-2021/IGC-Journals-21.12.zip --flatten_depth 0  # each top level folder is combined into a single file, results in a single file: IGC-Journals-21.12.txt
./extract_rmh.py -i /path/to/rmh-2021/IGC-Laws-21.05.zip --flatten_depth 0      # each top level folder is combined into a single file, results in a single file: IGC-Laws-21.05.txt
./extract_rmh.py -i /path/to/rmh-2021/IGC-News1-21.05.zip --flatten_depth 1     # top level folders are kept, results in a single under file: CC_BY/IGC-News1-21.05.txt
./extract_rmh.py -i /path/to/rmh-2021/IGC-News2-21.05.zip --flatten_depth 2     # two top levels of folders are kept, results in multiple files under MIM/IGC-News2-21.05.TEI/
./extract_rmh.py -i /path/to/rmh-2021/IGC-Parla-21.12.zip --flatten_depth 0     # each top level folder is combined into a single file, results in a single file: IGC-Parla-21.12.txt
./extract_rmh.py -i /path/to/rmh-2021/IGC-Social-21.10.zip  --flatten_depth 2   # two top levels of folders are kept, results in multiple files under TEI/IGC-Social-21.10.TEI/
```

For other options see `./extract_rmh.py --help`.

