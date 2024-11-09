# Dürer PDF generator for local contest

This scripts generates PDF files for the local contest. Each team gets a copy of each file in their category with their teamnames printed in the header. The final files are merged into a single PDF file for each location.

Tab-separated value (`.tsv`) files are used to define the files and the teams. In Google Sheet you can export a sheet to `.tsv` file.

## Install

It is recommended to use [virtual environment](https://docs.python.org/3/tutorial/venv.html). After that install the required packages:

```
pip install -r requirements.txt
```

## USAGE:

1) **PDF files:** Copy PDF files which need to be compiled in the folder `pdfsrc`.
2) **Category-wise files:** Create a `.tsv` file where you define how many copies of each file should be created for each team in specific category. (see `files.tsv.sample`)
3) **Team datas:** Create a `.tsv` file where you define what to print in the header of each team. (see `teamdatas.tsv.sample`)
4) Run the script
```
python do.py input_tsvs/files.tsv input_tsvs/teamdatas.tsv
```
Additional options:
```
--loglevel [DEBUG|INFO|WARNING|ERROR] (default: INFO)
--twosided: add blank page after each odd number of pages (default: False)
--force: ignore errors and continue (default: False)
```

This creates for all places (here `Budapest, VPG`) files like `target/Budapest, VPG/035-00.pdf`.
You might want to check out the generated PDFs for the weirder teamnames.

5) Merge the files for each location:
```
python merger.py --aftertext 1oldalas_feladatsor
```

## Debug

If some error happened you can try
- Running in debug level: `python do.py --loglevel=DEBUG`
- Checking the output file at target/location/n.tex. Which file failed should be easy to determine.
