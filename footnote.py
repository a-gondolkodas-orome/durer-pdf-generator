import io
from pypdf import PdfWriter, PdfReader
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

def writeover(input_fn, output_fn, data, twosided=False):
    pdfmetrics.registerFont(TTFont('MySerif', 'fonts/noto/GoNotoCurrent-Regular.ttf'))

    packet = io.BytesIO()
    can = canvas.Canvas(packet, pagesize=(A4[1], A4[0]))
    
    # Settings for text
    fontSize = 9
    can.setFont('MySerif', fontSize)
    page_width = A4[1]
    line_height = fontSize * 1.2  # spacing between lines
    
    # Split data into lines
    lines = data.split('\n')
    
    # Draw each line centered
    y_position = 22  # starting y position
    for line in reversed(lines):
        text_width = can.stringWidth(line, 'MySerif', fontSize)
        x = (page_width - text_width) / 2
        if text_width > page_width * 0.95:
            print(f"WARNING: Text too long, split the following line to more lines: {line}")
        can.drawString(x, y_position, line)
        y_position += line_height  # move up for next line
    
    can.showPage()
    can.save()

    packet.seek(0)
    new_pdf = PdfReader(packet)
    existing_pdf = PdfReader(open(input_fn, "rb"))
    output = PdfWriter()

    for i in range(len(existing_pdf.pages)):
        page = existing_pdf.pages[i]
        page.merge_page(new_pdf.pages[0])
        output.add_page(page)
        
    if twosided and (len(existing_pdf.pages) % 2 == 1):
        output.add_blank_page()

    outputStream = open(output_fn, "wb")
    output.write(outputStream)
    outputStream.close()

if __name__ == "__main__":
    writeover(
        "XVIII_KisDurer_eredmenyek.pdf",
        "output2.pdf",
        """A döntőbe jutás feltétele, hogy a csapat a saját helyszínén győzött (Q), vagy elérte a ponthatárt és iskolájából nem előzte meg egynél több csapat (q). A bejutókat Q és q jelöli"""
    )