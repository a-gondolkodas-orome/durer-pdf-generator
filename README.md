# durer-pdf-generator
Local contest problems with the teamnames printed in the header.

## USAGE:

0) Copy PDF files which need to be compiled in `pdfsrc/`.
1) Download team data in `Tab-separated value (.tsv, current sheet)` format to a file e.g. (`local.tsv`)
  - There is a live version for XV, ask for link. (3 columns for teamname, category and place)
2) At the start of `do.py` file, fill out the fields.
  - `possible_categories`: map category (name as in the TSV) to the corresponding main TEX file
  - `*_header`: The TSV file's header name which contains teamname, category and place
3) Run `python do.py local.tsv`
  - This creates for all places (here `VPG`) files like `target/VPG/105.pdf`.
  - You might want to check out the generated PDFs for the weirder teamnames.
4) Run `./merger.sh`
  - This needs `poppler`, which contains the `pdfunite` binary.
  - This creates `target/VPG.pdf` from all files in `target/VPG/*.pdf`.
5) You might need to tweak PDF overwrite generation in `overwrite` for special teamnames.

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
