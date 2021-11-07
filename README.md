# durer-local-handout
Local contest problems with the teamnames printed in the header.

## USAGE:

1) Create single-file TEX files to be generated in src/
2) Download team data in "Tab-separated value (.tsv, current sheet)" format e.g. (local.tsv)
3) In the TEX file provide \VAR{csapatnev} where the team name is to be written
4) In the head of do.py, fill out possible_categories; here point to the TEX files created (without src/)
5) Fix header names from CSV if it changed
6) Run `python do.py local.tsv`