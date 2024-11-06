import csv
import logging
import os
import shutil
import argparse
import sys
from typing import List

from PyPDF2 import PdfWriter, PdfReader #type:ignore
import io
from reportlab.pdfgen import canvas             #type:ignore
from reportlab.lib.pagesizes import A4          #type:ignore

from reportlab.pdfbase import pdfmetrics        #type:ignore
from reportlab.pdfbase.ttfonts import TTFont #type:ignore

def get_non_a4_pages(path):
    non_a4_pages = []
    if path in os.listdir("pdfsrc"):
        pdf = PdfReader(open(os.path.join("pdfsrc", path), "rb"))
        for i in range(len(pdf.pages)):
            width = pdf.pages[i].mediabox.width
            height = pdf.pages[i].mediabox.height
            tolerance = 1
            if abs(width - 595) > tolerance or abs(height - 842) > tolerance:
                non_a4_pages.append(i + 1)  # Page numbers are 1-based
    return non_a4_pages

def parsing():
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
6) If you want to create two-sided prining compatible outputs then use the --twosided option
7) by default, the script terminates if any pdf page is not of dimension A4. If you not want to apply this check use the option --force
""")
    parser.add_argument("--loglevel", choices=["DEBUG", "INFO", "WARNING", "ERROR"], nargs='?', default="INFO")
    parser.add_argument("--twosided", action="store_true")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("tsvfile")
    return parser.parse_args()

def set_headers(args):
    # itt add meg, hogy az input fájlban milyen header nevek szerepelnek
    args.category_header = 'Kategória'
    args.teamname_header = 'Csapatnév' # ez igazából nem a csapatnév, hanem a csapatnév + helyszín + terem
    args.place_header = 'Helyszín'

def init_categories(args):
    args.possible_categories = {}
    args.num = {}
    non_a4_pages = {}
    with open('files.tsv', 'r', encoding="utf8") as f:
        reader = csv.DictReader(f, delimiter='\t')
    for row in reader:
        if row['category'] not in args.possible_categories.keys():
            args.possible_categories[row['category']] = []
            args.num[row['category']] = []
        if int(row['copies']) > 0:
            args.possible_categories[row['category']].append(row['filename'])
            args.num[row['category']].append(int(row['copies']))
            current_non_a4_pages = get_non_a4_pages(row['filename'])
            if(len(current_non_a4_pages) > 0):
                non_a4_pages[row['filename']] = current_non_a4_pages
    if len(non_a4_pages) > 0 and not args.force:
        raise Exception(f"Non-A4 pages found in the following files and pages: {non_a4_pages}. If you want to proceed, use the --force option.")

    print("Categories: ", args.possible_categories)


def writeover(input_fn, output_fn, data, twosided=False):
    packet = io.BytesIO()
    # Create a new PDF with Reportlab
    can = canvas.Canvas(packet, pagesize=A4)
    can.rotate(90)
    can.setFont('MySerif', 10)
    # work-around for arabic.
    # HACK: Check for exact team name
    # TODO: C₈H₁₀N₄O₂
    # TODO: pi
	 # az arab karakterek benne vannak UNICODE-ban, így az alapján lehet őket a text-ben detektálni függvénnyel.
    #if "نحن أذكياء جدا" in data:
    #    can.setFont('Arab', 10)
    #    can.drawString(40, -30, data[:len("نحن أذكياء جدا")])
    #    can.setFont('MySerif', 10)
    #    can.drawString(100, -30, data[len("نحن أذكياء جدا"):])
    #else:
    #    can.drawString(40, -30, data)
    can.drawString(40, -30, data)
    can.showPage()
    can.save()

    # Move to the beginning of the StringIO buffer
    packet.seek(0)
    new_pdf = PdfReader(packet)
    # Read your existing PDF
    existing_pdf = PdfReader(open(input_fn, "rb"))
    output = PdfWriter()
    # Add the "watermark" (which is the new pdf) on the existing page
    for i in range(len(existing_pdf.pages)):
        page = existing_pdf.pages[i]
        page.merge_page(new_pdf.pages[0])
        output.add_page(page)
		
		# add blank page if the document has an odd number of pages
    if twosided and (len(existing_pdf.pages) % 2 == 1):
        output.add_blank_page()

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
    # TODO: nagyon hosszú csapatneveket trim-elni
    return s

def lpad(s, n):
    s = str(s)
    l = len(s)
    if l < n:
        return (n-l)*"0"+s
    return s


def handle_team(id, args, row=None, reserve=False):
#def handle_team(id, row=None, reserve=False, twosided=False):
    ids = lpad(id,3)
    logging.debug(f'Adding new team')
    category = row[args.category_header]
    teamname = row[args.teamname_header]
    place = row[args.place_header]
    ensure_dir(get_place_directory(place))

#    if place not in all_places:
#        all_places.append(place)

    original_pdfs = []
    num_copies_list = []

    if reserve:
        original_pdfs.append(os.path.join("pdfsrc", "tartalek.pdf"))
        num_copies_list.append(1) # reserve PDF contains all categories in needed number
    else:
        if category not in args.possible_categories:
            logging.error(f"Error: {category} not in {[*args.possible_categories.keys()]}. Skipping.")
        else:
            if isinstance(args.possible_categories[category], type([])) and isinstance(args.num[category], type([])):
                # multiple PDFs in a category
                for _, pdf in enumerate(args.possible_categories[category]): # Add all PDF to list
                    if pdf not in os.listdir("pdfsrc"):
                        logging.error(f"Error: {pdf} not in pdfsrc. Skipping.")
                    else:
                        original_pdfs.append(os.path.join("pdfsrc", pdf)) 
                        num_copies_list.append(args.num[category][_])
            else:
                # One PDF in a category
                if args.possible_categories[category] not in os.listdir("pdfsrc"):
                    logging.error(f"Error: {args.possible_categories[category]} not in pdfsrc. Skipping.")
                else:
                    original_pdfs.append(os.path.join("pdfsrc", args.possible_categories[category]))
                    num_copies_list.append(args.num[category])
    if len(original_pdfs) == 0:
        return

    # Instantiate templates
    # compile TEX file into PDF
    for pdf_number,original_pdf in enumerate(original_pdfs):
        if num_copies_list[pdf_number] == 0:
            break
        output_pdf = os.path.join("target", place, f"{ids}-{str(pdf_number).zfill(2)}.pdf")
        logging.info(f'Adding team {teamname} ({category} {place} #{ids}) {original_pdf} -> {output_pdf} (x{num_copies_list[pdf_number]})')
        try:
                writeover(original_pdf, output_pdf, sanitize_teamname(teamname), args.twosided)
        except Exception:
            logging.error(f"Error happened while writing over {original_pdf}")
            raise
    for pdf_number,num_copies in enumerate(num_copies_list):
        copy_counter = 0
        for _ in range(1, num_copies):
            copy_counter += 1
            shutil.copy(
                os.path.join('target', place, f"{ids}-{str(pdf_number).zfill(2)}.pdf"),
                os.path.join('target', place, f"{ids}-{str(pdf_number).zfill(2)}-{copy_counter}.pdf")
            )

def main():
    ###########################################
    # TODO: legyen opció, hogy üres olal hozzáadása helyett az utolsó oldalt rakja az "egyoldalas" kupacba
    # TODO: refactor it and the latex code -> szebb legyen a kód, kísérőlevél körlevelezés itt, ne latexben


    pdfmetrics.registerFont(TTFont('MySerif', 'fonts/noto/NotoSerif-Regular.ttf'))    # registers latin-based script
    #pdfmetrics.registerFont(TTFont('Arab', 'fonts/noto/NotoNaskhArabic-Regular.ttf'))    # registers arabic script

#    all_places:List[str] = []

    ############################################
    
    args = parsing()
    set_headers(args)
    init_categories(args)

    logging.basicConfig(level=args.loglevel)

    initialize_output_directories()

    try:
        with open(args.tsvfile, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter='\t', quotechar='"')
            id=0
            if len(set(reader.fieldnames)) != len(reader.fieldnames):
                pass#raise ValueError("Duplicate fieldname! Not going to proceed! Fix team table")
            for row in reader:
                handle_team(id, args, row)
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
