from collections import defaultdict
import csv
# from datetime import datetime
import logging
import os
import shutil
import argparse
# from typing import List
from tqdm import tqdm

from pypdf import PdfWriter, PdfReader
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

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
    parser = argparse.ArgumentParser(
        usage="""%(prog)s files_tsv_path team_data_tsv_path [options]
team_data_tsv_path: path to the TSV file containing the team data. 
Options:
    --loglevel [DEBUG|INFO|WARNING|ERROR] (default: INFO)
    --twosided: add blank page after each odd number of pages (default: False)
    --force: ignore errors and continue (default: False)"""
    )

    parser.add_argument("--loglevel", choices=["DEBUG", "INFO", "WARNING", "ERROR"], nargs='?', default="INFO")
    parser.add_argument("--twosided", action="store_true")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("files_tsv_path")
    parser.add_argument("team_data_tsv_path")
    return parser.parse_args()

def set_headers(args):
    # itt add meg, hogy az input fájlban milyen header nevek szerepelnek
    args.category_header = 'Kategória'
    args.teamname_header = 'Rövidített csapatnév (helyszín, terem)' # ez igazából nem a csapatnév, hanem a csapatnév + helyszín + terem
    args.place_header = 'Helyszín'

def init_categories(args):
    args.possible_categories = defaultdict(list)
    args.num = defaultdict(list)
    non_a4_pages = {}
    if not args.files_tsv_path.endswith('.tsv'):
        logging.error(f"The input file ({args.files_tsv_path}) is not a TSV file.")
    with open(args.files_tsv_path, 'r', encoding="utf8") as f:
        reader = csv.DictReader(f, delimiter='\t')
        for row in reader:
            if int(row['copies']) > 0:
                args.possible_categories[row['category']].append(row['filename'])
                args.num[row['category']].append(int(row['copies']))
                current_non_a4_pages = get_non_a4_pages(row['filename'])
                if(len(current_non_a4_pages) > 0):
                    non_a4_pages[row['filename']] = current_non_a4_pages
            else:
                logging.warning(f"Skipping {row['filename']} because copies is expected positive integer, but got {row['copies']}.")
    if len(non_a4_pages) > 0 and not args.force:
        logging.error(f"Non-A4 pages found in the following files and pages: {non_a4_pages}.")

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

def handle_team(id:str, args, row=None, reserve=False):
    id_str = str(id).zfill(3)
    logging.debug(f'Adding new team')
    category = row[args.category_header]
    teamname = row[args.teamname_header]
    place = row[args.place_header]
    os.makedirs(os.path.join('target', place), exist_ok=True)

    if category not in args.possible_categories.keys():
        logging.error(f"'{category}' not in set of possible categories: {[*args.possible_categories.keys()]}. Skipping line {id+2}.")
        return

    # Prepare the PDFs
    original_pdfs = []
    num_copies_list = []
    for pdf, copies in zip(args.possible_categories[category], args.num[category]):
        if not os.path.exists(os.path.join("pdfsrc", pdf)):
            logging.error(f"{pdf} not in pdfsrc. Skipping this page in line {id+2}.")
            continue
        original_pdfs.append(os.path.join("pdfsrc", pdf))
        num_copies_list.append(copies)

    # Create the PDFs
    for pdf_number, original_pdf_path in enumerate(original_pdfs):
        output_pdf_path = os.path.join("target", place, f"{id_str}-{str(pdf_number).zfill(2)}.pdf")
        logging.debug(f'Adding team {teamname} ({category} {place} #{id_str}) {original_pdf_path} -> {output_pdf_path} (x{num_copies_list[pdf_number]})')
        try:
            writeover(original_pdf_path, output_pdf_path, teamname, args.twosided)
        except Exception:
            logging.error(f"Error happened while writing over {original_pdf_path}")
            raise

    # Copy the PDFs
    for pdf_number, num_copies in enumerate(num_copies_list):
        for i in range(1, num_copies):
            shutil.copy(
                os.path.join('target', place, f"{id_str}-{str(pdf_number).zfill(2)}.pdf"),
                os.path.join('target', place, f"{id_str}-{str(pdf_number).zfill(2)}-{i}.pdf")
            )

def read_tsv_file(team_data_tsv_path, expected_fieldnames):
    rows = []
    if not team_data_tsv_path.endswith('.tsv'):
        logging.error(f"The input file ({team_data_tsv_path}) is not a TSV file.")
    with open(team_data_tsv_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter='\t', quotechar='"')
        if set(reader.fieldnames) != expected_fieldnames:
            raise ValueError("Column names do not match. Expected: %s, got: %s" % (expected_fieldnames, reader.fieldnames))
        for row in reader:
            rows.append(row)
    return rows

class ErrorRaisingHandler(logging.Handler):
    def __init__(self, force=False):
        super().__init__()
        self.force = force
    def emit(self, record):
        if record.levelno == logging.ERROR and not self.force:
            raise RuntimeError(record.getMessage())

def configure_logging(args):
    # TODO: save to log file?
    # os.makedirs("logs", exist_ok=True)
    # current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
    # log_filename = os.path.join("logs", f"log_{current_time}.log")
    logging.basicConfig(
        level=args.loglevel,
        # filename=log_filename,
        # filemode='w',
        # format='%(asctime)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger()
    logger.addHandler(ErrorRaisingHandler(args.force))

if __name__ == "__main__":
    ###########################################
    # TODO: legyen opció, hogy üres olal hozzáadása helyett az utolsó oldalt rakja az "egyoldalas" kupacba
    # TODO: refactor it and the latex code -> szebb legyen a kód, kísérőlevél körlevelezés itt, ne latexben
    # TODO: nagyon hosszú csapatneveket trim-elni


    pdfmetrics.registerFont(TTFont('MySerif', 'fonts/noto/NotoSerif-Regular.ttf'))    # registers latin-based script
    #pdfmetrics.registerFont(TTFont('Arab', 'fonts/noto/NotoNaskhArabic-Regular.ttf'))    # registers arabic script

#    all_places:List[str] = []

    ############################################
    
    args = parsing()
    set_headers(args)
    init_categories(args)

    configure_logging(args)

    os.makedirs("target", exist_ok=True)
    if len(os.listdir("target")) > 0:
        logging.warning("The target directory is not empty. Files may be overwritten.")

    expected_fieldnames = set([args.teamname_header, args.category_header, args.place_header])
    rows = read_tsv_file(args.team_data_tsv_path, expected_fieldnames)
    for id, row in tqdm(enumerate(rows), total=len(rows)):
        handle_team(id, args, row)
    logging.info("Single files are created in the target directory. You can merge them with merger.py.")