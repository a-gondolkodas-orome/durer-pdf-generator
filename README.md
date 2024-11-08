# Dürer PDF generator for local contest

This scripts generates PDF files for the local contest. Each team gets a copy of each file in their category with the teamnames printed in the header. The final files are merged into a single PDF file for each location.

## USAGE:

1) **PDF files:** Copy PDF files which need to be compiled in the folder `pdfsrc`.
2) **Category-wise files:** Create a file like `debug_files.tsv` where you define how many copies of each file should be created for each team in specific category.
3) **Team datas:** Download team data in `Tab-separated value (.tsv)` format to a file like `debug_teamdatas.tsv`.
3) Run the script
```
python do.py input_tsvs/files.tsv input_tsvs/teamdatas.tsv
```
Additional options:
```
--loglevel [DEBUG|INFO|WARNING|ERROR] (default: INFO)
--twosided: add blank page after each odd number of pages (default: False)
--force: ignore errors and continue (default: False)
```

- This creates for all places (here `VPG`) files like `target/VPG/105.pdf`.
- You might want to check out the generated PDFs for the weirder teamnames.
4) Run `./merger.sh`
  - This needs `poppler`, which contains the `pdfunite` binary.
  - This creates `target/VPG.pdf` from all files in `target/VPG/*.pdf`.

# Local XV. Dürer -- write-up

For future reference.

## Preprocess

I preprocessed some PDFs: I've merged

- `K` + paper
- `K+` + paper 
- (every category already in correct multiplicity) -> `reserve.pdf`
  - meaning that reserve.pdf contains 3 copies of C category things.

Also, I've prepared the data from teams in Excel (cross-referencing team name+category with Budapest contestants[^1]). There were 2 issues: 2 teams were registered outside Budapest, but were present in the Budapest sheet.

[^1]: this sheet contains the exact place in Budapest where they will write the contest (e.g. ELTE or VPG).

## Post-process

This merges all PDFs from a single place.

There is a tool `merger.sh` which does this job (see Usage)

## Debug

If some error happened you can try
- Running in debug level: python do.py --loglevel=DEBUG
- Checking the output file at target/location/n.tex. Which file failed should be easy to determine.
