import csv
import logging
import os
import shutil
import argparse
from typing import List

from PyPDF2 import PdfFileWriter, PdfFileReader #type:ignore
import io
from reportlab.pdfgen import canvas             #type:ignore
from reportlab.lib.pagesizes import A4          #type:ignore

from reportlab.pdfbase import pdfmetrics        #type:ignore



'''
USAGE:
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
'''

# TODO: support ranges in a PDF file
# TODO: refactor it and the latex code
with open('files.tsv', 'r', encoding="utf8") as f:
    reader = csv.DictReader(f, delimiter='\t')
    possible_categories = {}
    num = {}
    for row in reader:
        if row['category'] not in possible_categories.keys():
            possible_categories[row['category']] = []
            num[row['category']] = []
        possible_categories[row['category']].append(row['filename'])
        num[row['category']].append(int(row['copies']))

category_header = 'Kategória'
teamname_header = 'Csapatnév'
place_header = 'Helyszín'

from reportlab.pdfbase.ttfonts import TTFont #type:ignore

pdfmetrics.registerFont(TTFont('MySerif', 'fonts/noto/NotoSerif-Regular.ttf'))
pdfmetrics.registerFont(TTFont('Arab', 'fonts/noto/NotoNaskhArabic-Regular.ttf'))


def writeover(input_fn, output_fn, data):
    packet = io.BytesIO()
    # Create a new PDF with Reportlab
    can = canvas.Canvas(packet, pagesize=A4)
    can.rotate(90)
    can.setFont('MySerif', 10)
    # work-around for arabic.
    # HACK: Check for exact team name
    if "نحن أذكياء جدا" in data:
        can.setFont('Arab', 10)
        can.drawString(40, -30, data[:len("نحن أذكياء جدا")])
        can.setFont('MySerif', 10)
        can.drawString(100, -30, data[len("نحن أذكياء جدا"):])
    else:
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

def sanitize_teamname(s):
    return s

def writeover0(input_fn, output_pdf, csapatnev, helyszin):
    writeover(input_fn, output_pdf, f"{csapatnev} ({helyszin})")

def lpad(s, n):
    s = str(s)
    l = len(s)
    if l < n:
        return (n-l)*"0"+s
    return s

all_places:List[str] = []

def handle_team(id, row=None, reserve=False):
    ids = lpad(id,3)
    logging.debug(f'Adding new team')
    category = row[category_header]
    teamname = row[teamname_header]
    place = row[place_header]
    ensure_dir(get_place_directory(place))

    if place not in all_places:
        all_places.append(place)

    original_pdfs = []
    num_copies_list = []

    if reserve:
        original_pdfs.append(os.path.join("pdfsrc", "tartalek.pdf"))
        num_copies_list.append(1) # reserve PDF contains all categories in needed number
    else:
        if category not in all_possible_categories:
            logging.error(f"Error: {category} not in {[*all_possible_categories.keys()]}. Skipping.")
        else:
            if isinstance(all_possible_categories[category], type([])) and isinstance(num[category], type([])):
                # multiple PDFs in a category
                for _, pdf in enumerate(all_possible_categories[category]): # Add all PDF to list
                    if pdf not in os.listdir("pdfsrc"):
                        logging.error(f"Error: {pdf} not in pdfsrc. Skipping.")
                    else:
                        original_pdfs.append(os.path.join("pdfsrc", pdf)) 
                        num_copies_list.append(num[category][_])
            else:
                # One PDF in a category
                if all_possible_categories[category] not in os.listdir("pdfsrc"):
                    logging.error(f"Error: {all_possible_categories[category]} not in pdfsrc. Skipping.")
                else:
                    original_pdfs.append(os.path.join("pdfsrc", all_possible_categories[category]))
                    num_copies_list.append(num[category])
    if len(original_pdfs) == 0:
        return

    # Instantiate templates
    # compile TEX file into PDF
    for pdf_number,original_pdf in enumerate(original_pdfs):
        if num_copies_list[pdf_number] == 0:
            break
        output_pdf = os.path.join("target", place, f"{ids}-{pdf_number}.pdf")
        logging.info(f'Adding team {teamname} ({category} {place} #{ids}) {original_pdf} -> {output_pdf} (x{num_copies_list[pdf_number]})')
        try:
                writeover0(original_pdf, output_pdf, csapatnev=sanitize_teamname(teamname), helyszin=place)
        except Exception:
            logging.error(f"Error happened while writing over {original_pdf}")
            raise
    for pdf_number,num_copies in enumerate(num_copies_list):
        copy_counter = 0
        for _ in range(1, num_copies):
            copy_counter += 1
            shutil.copy(
                os.path.join('target', place, f"{ids}-{pdf_number}.pdf"),
                os.path.join('target', place, f"{ids}-{pdf_number}-{copy_counter}.pdf")
            )

def main():
    parser = argparse.ArgumentParser(usage="""
USAGE:
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
""")
    parser.add_argument("--loglevel", choices=["DEBUG", "INFO", "WARNING", "ERROR"], nargs='?', default="INFO")
    parser.add_argument("tsvfile")
    args = parser.parse_args()
    logging.basicConfig(level=args.loglevel)

    initialize_output_directories()

    try:
        with open(args.tsvfile, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter='\t', quotechar='"')
            id=0
            if len(set(reader.fieldnames)) != len(reader.fieldnames):
                pass#raise ValueError("Duplicate fieldname! Not going to proceed! Fix team table")
            for row in reader:
                handle_team(id, row)
                id += 1
            # reserve for every place. In separately generated PDF.
#            for place in all_places:
#                handle_team(id, {
#                    category_header: 'reserve',
#                    teamname_header: "TARTALÉK",
#                    place_header: place
#                }, reserve=True)
#                id += 1
    except Exception:
        print("Some error happened. If it was parsing, try")
        print("  - Running in debug level: python do.py --loglevel=DEBUG")
        print("  - Checking the output file at target/location/n.tex. Which file failed should be easy to determine.")
        raise

main()
