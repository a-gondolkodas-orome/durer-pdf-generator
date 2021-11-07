# durer-local-handout
Local contest problems with the teamnames printed in the header.

USAGE:

0) create single-file TEX files to be generated in src/
1) In the TEX file provide \VAR{csapatnev} where the team name is to be written
2) In the head of do.py, fill out possible_categories; here point to the TEX files created (without src/)
3) Fix header names from CSV if it changed
4) Run `python do.py`
