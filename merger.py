import os
import logging
from pypdf import PdfWriter

def merge_pdfs():
    os.chdir('target')
    places = [d for d in os.listdir(".") if os.path.isdir(d)]
    for place in places:
        merger = PdfWriter()
        files = [os.path.join(place, f) for f in os.listdir(place) if f.endswith('.pdf')]        
        for pdf in files:
            merger.append(pdf)
        output_path = f"{place}.pdf"
        if os.path.exists(output_path):
            logging.warning(f"File {output_path} already exists. Overwriting.")
        merger.write(output_path)
        merger.close()
    os.chdir('..')

if __name__ == "__main__":
    merge_pdfs()