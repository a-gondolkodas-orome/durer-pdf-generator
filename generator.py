from collections import defaultdict
import logging
import os
import shutil
import argparse
from typing import Literal, Dict, List
from venv import logger
from tqdm import tqdm
import pandas as pd
from pydantic import BaseModel
from pypdf import PdfWriter, PdfReader
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

CATEGORY_HEADER = "Kategória"
TEAMNAME_HEADER = "Rövidített csapatnév (helyszín, terem)"
PLACE_HEADER = "Helyszín"


class CompetitionFile(BaseModel):
    category: str
    filename: str
    copies: int
    duplex: Literal["", "duplex", "simplex"]


type FilesDict = Dict[str, List[CompetitionFile]]


def get_non_a4_pages(path):
    full_path = os.path.join("pdfsrc", path)
    if not os.path.exists(full_path):
        logger.error(f"{full_path} does not exist. Cannot check page sizes.")
        return []
    non_a4_pages = []
    pdf = PdfReader(open(full_path, "rb"))
    for i in range(len(pdf.pages)):
        width = pdf.pages[i].mediabox.width
        height = pdf.pages[i].mediabox.height
        tolerance = 1
        if abs(width - 595) > tolerance or abs(height - 842) > tolerance:
            non_a4_pages.append(i + 1)  # Page numbers are 1-based
    return non_a4_pages


def get_page_count(path):
    """Get the number of pages in a PDF file."""
    full_path = os.path.join("pdfsrc", path)
    if not os.path.exists(full_path):
        logger.error(f"{full_path} does not exist. Cannot get page count.")
        return 0
    pdf = PdfReader(open(full_path, "rb"))
    return len(pdf.pages)


def validate_duplex_setting(filename: str, duplex_value: str):
    """Validate duplex setting based on page count and --twosided flag."""
    page_count = get_page_count(filename)
    if page_count == 0:
        raise ValueError(f"Page count is 0 for {filename}")

    # For 1-page PDFs, duplex must be empty
    if page_count == 1:
        if duplex_value != "":
            raise ValueError(
                f"For 1-page PDF ({filename}), duplex column must be empty, but got '{duplex_value}'"
            )
        return

    # For multi-page PDFs, duplex must be "duplex" or "simplex"
    if duplex_value not in ["duplex", "simplex"]:
        raise ValueError(
            f"For multi-page PDF ({filename} - {page_count} pages) - duplex column must be 'duplex' or 'simplex', but got '{duplex_value}'"
        )


def parsing():
    parser = argparse.ArgumentParser(
        usage="""%(prog)s files_tsv_path team_data_tsv_path [options]
team_data_tsv_path: path to the TSV file containing the team data. 
Options:
    --loglevel [DEBUG|INFO|WARNING|ERROR] (default: INFO)
    --twosided: add blank page after each odd number of pages (default: False)
    --force: ignore errors and continue (default: False)
    --from_line [line_number]: start from this line in the team data file (default: 1)
    """
    )

    parser.add_argument(
        "--loglevel",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        nargs="?",
        default="INFO",
    )
    parser.add_argument("--twosided", action="store_true")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--from_line", type=int, default=1)
    parser.add_argument("files_tsv_path")
    parser.add_argument("team_data_tsv_path")
    return parser.parse_args()


def load_and_validate_files_tsv(args) -> FilesDict:
    """Read and validate the files TSV, and return it as a FilesDict."""
    if not args.files_tsv_path.endswith(".tsv"):
        logging.error(f"The input file ({args.files_tsv_path}) is not a TSV file.")

    # Read files TSV using pandas
    files_df = pd.read_csv(
        args.files_tsv_path,
        sep="\t",
        dtype={"category": str, "filename": str, "copies": int, "duplex": str},
        keep_default_na=False,
    )

    # Filter out rows with copies <= 0
    invalid_copies = files_df[files_df["copies"] <= 0]
    for _, row in invalid_copies.iterrows():
        logging.warning(
            f"Skipping {row['filename']} because copies is expected positive integer, but got {row['copies']}."
        )
    files_df = files_df[files_df["copies"] > 0]

    # Validate duplex settings
    if args.twosided:
        for _, row in files_df.iterrows():
            validate_duplex_setting(str(row["filename"]), str(row["duplex"]))

    # Check for non-A4 pages
    non_a4_pages = {}
    for filename in files_df["filename"].unique():
        current_non_a4_pages = get_non_a4_pages(filename)
        if len(current_non_a4_pages) > 0:
            non_a4_pages[filename] = current_non_a4_pages
    if len(non_a4_pages) > 0 and not args.force:
        logging.error(
            f"Non-A4 pages found in the following files and pages: {non_a4_pages}."
        )

    # Convert to dict
    files_dict: Dict[str, List[CompetitionFile]] = defaultdict(list)
    for _, row in files_df.iterrows():
        files_dict[str(row["category"])].append(
            CompetitionFile(
                category=str(row["category"]),
                filename=str(row["filename"]),
                copies=int(row["copies"]),
                duplex=str(row["duplex"]),
            )
        )

    return files_dict


def add_watermark_and_blank_pages_to_pdf(
    input_fn, output_fn, data, twosided=False, duplex_setting=""
):
    packet = io.BytesIO()
    # Create a new PDF with Reportlab
    can = canvas.Canvas(packet, pagesize=A4)
    can.rotate(90)
    can.setFont("MySerif", 10)
    # work-around for arabic.
    # if "نحن أذكياء جدا" in data:
    #    can.setFont('Arab', 10)
    #    can.drawString(40, -30, data[:len("نحن أذكياء جدا")])
    #    can.setFont('MySerif', 10)
    #    can.drawString(100, -30, data[len("نحن أذكياء جدا"):])
    # else:
    #    can.drawString(40, -30, data)
    can.drawString(40, -30, data)
    can.showPage()
    can.save()

    packet.seek(0)  # Move to the beginning of the StringIO buffer
    watermarked_pdf = PdfReader(packet)
    existing_pdf = PdfReader(open(input_fn, "rb"))
    output = PdfWriter()

    # Add the "watermark" (which is the new pdf) on the existing page
    # Handle blank page insertion based on duplex setting
    if twosided and duplex_setting == "simplex":
        # For simplex: add blank page after every page
        for i in range(len(existing_pdf.pages)):
            page = existing_pdf.pages[i]
            page.merge_page(watermarked_pdf.pages[0])
            output.add_page(page)
            output.add_blank_page()
    else:
        # For duplex or empty (1-page): add pages normally
        for i in range(len(existing_pdf.pages)):
            page = existing_pdf.pages[i]
            page.merge_page(watermarked_pdf.pages[0])
            output.add_page(page)

        # Add blank page at end if duplex/empty and odd page count
        if twosided and (len(existing_pdf.pages) % 2 == 1):
            output.add_blank_page()

    # Finally, write "output" to a real file
    outputStream = open(output_fn, "wb")
    output.write(outputStream)
    outputStream.close()


def process_team(id: int, files_dict: FilesDict, row: pd.Series, twosided: bool):
    id_str = str(id).zfill(3)
    category = str(row[CATEGORY_HEADER])
    teamname = str(row[TEAMNAME_HEADER])
    place = str(row[PLACE_HEADER])
    logging.debug(f"Adding new team {teamname} ({category} {place} #{id_str})")
    os.makedirs(os.path.join("target", place), exist_ok=True)

    # Get files for this category from FilesDict
    category_files = files_dict[category]
    if len(category_files) == 0:
        logging.error(
            f"'{category}' not in set of possible categories: {files_dict.keys()}. Skipping line {id+2}."
        )
        return

    # Create the PDFs
    pdf_number = 0
    for file in category_files:
        original_pdf_path = os.path.join("pdfsrc", file.filename)

        if not os.path.exists(original_pdf_path):
            logging.error(
                f"{file.filename} not in pdfsrc. Skipping this page in line {id+2}."
            )
            continue

        output_pdf_path = os.path.join(
            "target", place, f"{id_str}-{str(pdf_number).zfill(2)}.pdf"
        )
        logging.debug(
            f"Adding team {teamname} ({category} {place} #{id_str}) {original_pdf_path} -> {output_pdf_path} (x{file.copies})"
        )

        try:
            add_watermark_and_blank_pages_to_pdf(
                original_pdf_path, output_pdf_path, teamname, twosided, file.duplex
            )
        except Exception:
            logging.error(f"Error happened while writing over {original_pdf_path}")
            raise

        # Copy the PDF if copies > 1
        for i in range(1, file.copies):
            shutil.copy(
                output_pdf_path,
                os.path.join(
                    "target", place, f"{id_str}-{str(pdf_number).zfill(2)}-{i}.pdf"
                ),
            )

        pdf_number += 1


def read_tsv_file(team_data_tsv_path: str) -> pd.DataFrame:
    if not team_data_tsv_path.endswith(".tsv"):
        raise ValueError(f"The input file ({team_data_tsv_path}) is not a TSV file.")

    team_df = pd.read_csv(
        team_data_tsv_path,
        sep="\t",
        dtype={
            TEAMNAME_HEADER: str,
            CATEGORY_HEADER: str,
            PLACE_HEADER: str,
        },
        keep_default_na=False,
    )

    return team_df


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


def prepare_target_dir(places):
    os.makedirs("target", exist_ok=True)
    if len(os.listdir("target")) > 0:
        logging.warning(
            "The target directory is not empty. Files may be overwritten when merging files."
        )
    for place in places:
        if "/" in place or "\\" in place:
            logging.error(f"Place name {place} contains a slash. Please remove it.")
        place_dir = os.path.join("target", place)
        os.makedirs(place_dir, exist_ok=True)
        if len(os.listdir(place_dir)) > 0:
            logging.error(
                f"The target directory for {place} is not empty. This can cause silent bugs."
            )


if __name__ == "__main__":
    ###########################################
    # TODO: legyen opció, hogy üres olal hozzáadása helyett az utolsó oldalt rakja az "egyoldalas" kupacba
    # TODO: refactor it and the latex code -> szebb legyen a kód, kísérőlevél körlevelezés itt, ne latexben
    # TODO: nagyon hosszú csapatneveket trim-elni

    # pdfmetrics.registerFont(TTFont('MySerif', 'fonts/noto/NotoSerif-Regular.ttf'))
    # https://github.com/satbyy/go-noto-universal
    pdfmetrics.registerFont(TTFont("MySerif", "fonts/noto/GoNotoCurrent-Regular.ttf"))
    # pdfmetrics.registerFont(TTFont('MySerif', 'NotoEmoji-VariableFont_wght.ttf'))

    args = parsing()
    files_dict = load_and_validate_files_tsv(args)

    configure_logging(args)

    team_df = read_tsv_file(args.team_data_tsv_path)

    prepare_target_dir(set(team_df[PLACE_HEADER].unique()))

    for id in tqdm(range(args.from_line - 1, len(team_df))):
        process_team(id, files_dict, team_df.iloc[id], args.twosided)
    logging.info(
        "Single files are created in the target directory. You can merge them with merger.py."
    )
