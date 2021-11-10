import csv
import logging
import os
from subprocess import Popen, DEVNULL
import jinja2
from jinja2.environment import Template
import tempfile
import shutil
import argparse

from PyPDF2 import PdfFileWriter, PdfFileReader
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4

'''
USAGE:
0) Copy TEX files which need to be compiled in `src/`.
  - The current working directory will be `src/`, meaning that it works similar to Overleaf
1) Download team data in `Tab-separated value (.tsv, current sheet)` format to a file e.g. (`local.tsv`)
  - There is a live version for XV, ask for link. (3 columns for teamname, category and place)
2) In the TEX file provide `\VAR{csapatnev}` and `\VAR{helyszin}` where the team name or place is needed
  - For files where this is needed, rename `something.tex` to `something.tex.j2`.
  - The software will create `something.tex` for every separate file before compiling.
3) At the start of do.py, fill out the fields.
  - `possible_categories`: map category (name as in the TSV) to the corresponding main TEX file
  - `templated_files`: a list of every file where data needs to be rewritten in any categories.
  - `*_header`: The TSV file's header name which contains teamname, category and place
4) Run `python do.py local.tsv`
  - This needs a full setup of PDFLaTeX (with all the necessary packages).
  - This creates for all places (here `VPG`) files like `target/VPG/105.pdf`.
  - Log files are also here.
  - You might want to check out the generated PDFs for strange teamnames.
5) Run `./merger.sh`
  - This needs `poppler`, which contains the `pdfunite` binary.
  - This creates `target/VPG.pdf` from all files in `target/VPG/*.pdf`.
'''

possible_categories = {
    'C kategória': 'C_vegleges_v2.pdf',
    'D kategória': 'D_vegleges_v2.pdf',
    'E kategória': 'E_vegleges.pdf',
    'E+ kategória': 'Eplusz_vegleges.pdf',
    'F kategória': 'F2021.pdf',
    'F+ kategória': 'Fpluß2021.pdf',
    'K kategória': '15IK-es-cikk.pdf',
    'K+ kategória': '15IKplusz-es-cikk.pdf',
    }
num = {
    'C kategória': 3,
    'D kategória': 3,
    'E kategória': 3,
    'E+ kategória': 3,
    'F kategória': 3,
    'F+ kategória': 3,
    'K kategória': 1,
    'K+ kategória': 1,
    }

category_header = 'Kategória'
teamname_header = 'Csapatnév'
place_header = 'Helyszín'

# Additional packages to be used for weird characters
packages='''
\\usepackage{fancyvrb}
'''

def writeover(input_fn, output_fn, data):
    packet = io.BytesIO()
    # Create a new PDF with Reportlab
    can = canvas.Canvas(packet, pagesize=A4)
    can.rotate(90)
    can.setFont('Helvetica-Bold', 10)
    can.drawString(40, -30, data)
    can.showPage()
    can.save()

    # Move to the beginning of the StringIO buffer
    packet.seek(0)
    new_pdf = PdfFileReader(packet)
    # Read your existing PDF
    existing_pdf = PdfFileReader(open(input_fn, "rb"))
    output = PdfFileWriter()
    # Add the "watermark" (which is the new pdf) on the existing page
    for i in range(existing_pdf.getNumPages()):
        page = existing_pdf.getPage(i)
        page.mergePage(new_pdf.getPage(0))
        output.addPage(page)
    # Finally, write "output" to a real file
    outputStream = open(output_fn, "wb")
    output.write(outputStream)
    outputStream.close()

# I/O
def get_place_directory(place):
    return os.path.join('target', place)

def ensure_dir(path):
    if not os.path.isdir(path):
        os.mkdir(path)
def initialize_output_directories():
    ensure_dir('target')


class LatexCompileError(Exception):
    def __init__(self, *args):
        super().__init__(*args)

def sanitize_teamname(s):
    return s
    # exact team names that LaTeX cannot handle without special care
    if s == "نحن أذكياء جدا":
        return "\\textRL{نحن أذكياء جدا}"
    elif s == "⠀": # this is a braille space, one of the team's name
        return "\\texttt{ }"
    # exact characters
    s = s.replace('_', '\\_')
    s = s.replace('$', '\\$')
    s = s.replace('^', '$\\hat{\\ }$') # TODO is there a better solution?
    return "\\texttt{\\Verb|" + s + "|}" # \usepackage{fancyvrb}

def writeover0(input_fn, output_pdf, csapatnev, helyszin):
    writeover(input_fn, output_pdf, f"{csapatnev} ({helyszin})")

def lpad(s, n):
    s = str(s)
    l = len(s)
    if l < n:
        return (n-l)*"0"+s
    return s

#place_to_all_categories = {
#
#}

def handle_team(id, row):
    ids = lpad(id,3)
    logging.debug(f'Adding new team')
    category = row[category_header]
    teamname = row[teamname_header]
    place = row[place_header]
    output_pdf = os.path.join("target", place, f"{ids}.pdf")
    good = True # write all warnings
    logging.info(f'Adding team {teamname} ({category} {place} #{ids})')
    ensure_dir(get_place_directory(place))

    if category not in possible_categories:
        logging.error(f"Error: {category} not in {[*possible_categories.keys()]}. Skipping.")
        good = False
    if not good:
        return

    # Instantiate templates
    # compile TEX file into PDF
    original_pdf = os.path.join("pdfsrc", possible_categories[category])
    logging.debug(f"{teamname}; {place}; {category} -> {output_pdf}")
    try:
        writeover0(original_pdf, output_pdf, csapatnev=sanitize_teamname(teamname),
            helyszin=place)
    except Exception:
        logging.error(f"Error happened while writing over {original_pdf}")
        raise
    for i in range(1, num[category]):
        shutil.copy(
            os.path.join('target', place, f"{ids}.pdf"),
            os.path.join('target', place, f"{ids}-{i}.pdf")
        )

def main():
    parser = argparse.ArgumentParser(usage="""
USAGE:
0) Copy TEX files which need to be compiled in `src/`.
  - The current working directory will be `src/`, meaning that it works similar to Overleaf
1) Download team data in `Tab-separated value (.tsv, current sheet)` format to a file e.g. (`local.tsv`)
  - There is a live version for XV, ask for link. (3 columns for teamname, category and place)
2) In the TEX file provide `\VAR{csapatnev}` and `\VAR{helyszin}` where the team name or place is needed
  - For files where this is needed, rename `something.tex` to `something.tex.j2`.
  - The software will create `something.tex` for every separate file before compiling.
3) At the start of do.py, fill out the fields.
  - `possible_categories`: map category (name as in the TSV) to the corresponding main TEX file
  - `templated_files`: a list of every file where data needs to be rewritten in any categories.
  - `*_header`: The TSV file's header name which contains teamname, category and place
4) Run `python do.py local.tsv`
  - This needs a full setup of PDFLaTeX (with all the necessary packages).
  - This creates for all places (here `VPG`) files like `target/VPG/105.pdf`.
  - Log files are also here.
  - You might want to check out the generated PDFs for strange teamnames.
5) Run `./merger.sh`
  - This needs `poppler`, which contains the `pdfunite` binary.
  - This creates `target/VPG.pdf` from all files in `target/VPG/*.pdf`.
""")
    parser.add_argument("--loglevel", choices=["DEBUG", "INFO", "WARNING", "ERROR"], nargs='?', default="INFO")
    parser.add_argument("tsvfile")
    args = parser.parse_args()
    logging.basicConfig(level=args.loglevel)

    initialize_output_directories()

    try:
        with open(args.tsvfile, 'r', newline='') as f:
            reader = csv.DictReader(f, delimiter='\t', quotechar='"')
            id=0
            if len(set(reader.fieldnames)) != len(reader.fieldnames):
                pass#raise ValueError("Duplicate fieldname! Not going to proceed! Fix team table")
            for row in reader:
                handle_team(id, row)
                id += 1
    except Exception:
        print("Some error happened. If it was parsing, try")
        print("  - Running in debug level: python do.py --loglevel=DEBUG")
        print("  - Checking the output file at target/location/n.tex. Which file failed should be easy to determine.")
        raise

main()
