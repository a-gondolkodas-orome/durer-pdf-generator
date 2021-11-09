#!/bin/bash

#After using `do.py` to create PDFs for every team,
#Use this to merge all places into one. Retains order of teams.

cd target
for place in *; do
    pdfunite "$place"/*.pdf "$place".pdf
done