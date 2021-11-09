# durer-local-handout
Local contest problems with the teamnames printed in the header.

## USAGE:

1) Create single-file TEX files to be generated in src/
2) Download team data in "Tab-separated value (.tsv, current sheet)" format e.g. (local.tsv)
3) In the TEX file provide \VAR{csapatnev} where the team name is to be written
4) In the head of do.py, fill out possible_categories; here point to the TEX files created (without src/)
5) Fix header names from CSV if it changed
6) Run `python do.py local.tsv`

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