import argparse
import os
import logging
from pypdf import PdfWriter
from tqdm import tqdm


def merge_pdfs():
    parser = argparse.ArgumentParser(usage="""%(prog)s [options]
Options:
    --aftertext [text]: text to be added after each PDF file (default: None)
    """)
    parser.add_argument("--aftertext", nargs='?', default=None)
    args = parser.parse_args()

    os.chdir('target')
    places = [d for d in os.listdir(".") if os.path.isdir(d)]
    for place in tqdm(places):
        merger = PdfWriter()
        files = [os.path.join(place, f) for f in os.listdir(place) if f.endswith('.pdf')]        
        for pdf in files:
            merger.append(pdf)
        after_text = ""
        if args.aftertext is not None:
            after_text = "_" + args.aftertext
        output_path = f"{place}{after_text}.pdf"
        if os.path.exists(output_path):
            logging.warning(f"File {output_path} already exists. Overwriting.")
        merger.write(output_path)
        merger.close()
    os.chdir('..')

if __name__ == "__main__":
    merge_pdfs()