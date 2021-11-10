# durer-local-handout
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

## Templating in the margin

The template file was modified like this (for the math latex file):

```diff
*** magic/feladat.tex  2021-11-09 15:18:56.482105439 +0100
--- magic/feladat.tex   2021-11-09 15:20:38.903300985 +0100
*** 15,20 ****
      }[\PackageError{tree}{Undefined option to tree: #1}{}]%
  }%
  
+ \usepackage{marginnote}
  \usepackage{amssymb}
  \usepackage{amsmath}
  \usepackage{enumitem}
*** 48,58 ****
  \def\cm{\text{cm}}
  \def\szog{\sphericalangle}
  
  
  \begin{document}
  \fancyhf{}
  \tree{\nyelv}
- \chead{\includegraphics[width=17cm]{fejlecek/\kat_\nyelv_feladat.jpg}}
  
  \normalsize
  
*** 49,60 ****
  \def\cm{\text{cm}}
  \def\szog{\sphericalangle}
  
+ \reversemarginpar
  
  \begin{document}
  \fancyhf{}
  \tree{\nyelv}
+ \chead{\includegraphics[width=17cm]{fejlecek/\kat_\nyelv_feladat.jpg}\marginnote{\rotatebox[origin=r]{90}{\VAR{csapatnev}}}}
  
  \normalsize
```

This adds a margin next to `\chead` (which overflows the header, which gives a warning). `\usepackage{marginnote}` and `\marginnote` is used so that it the margin itself is not a float (which would prevent usage in `\chead`). This also means that all pages contain the team's name.

The text is rotated (the rotation is pinned to the right side of the text; i.e. that stays in place). This means that for very long team names only the last part is visible. This may need manual intervention.

`\reversemarginpar` is used so that the *left* margin is used (the problem page is one-sided).