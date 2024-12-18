import io
from pypdf import PdfWriter, PdfReader
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch

def get_wrapped_text(text, font_name, font_size, max_width):
    from reportlab.pdfgen import canvas
    from io import BytesIO
    
    buffer = BytesIO()
    c = canvas.Canvas(buffer)
    c.setFont(font_name, font_size)
    
    words = text.split()
    lines = []
    current_line = words[0]
    
    for word in words[1:]:
        if c.stringWidth(current_line + ' ' + word) <= max_width:
            current_line += ' ' + word
        else:
            lines.append(current_line)
            current_line = word
    
    lines.append(current_line)
    
    return '\n'.join(lines)

def get_text_height(text, font_name, font_size, max_width):
    wrapped_text = get_wrapped_text(text, font_name, font_size, max_width)
    return (wrapped_text.count('\n') + 1) * (font_size + 2)  # Add 2 points of leading

def writeover(input_fn, output_fn, data):
    pdfmetrics.registerFont(TTFont('MySerif', 'fonts/noto/GoNotoCurrent-Regular.ttf'))

    packet = io.BytesIO()
    can = canvas.Canvas(packet, pagesize=(A4[1], A4[0]))
    
    # Settings for text
    fontSize = 9
    can.setFont('MySerif', fontSize)
    page_width = A4[1]
    line_height = fontSize * 1.2  # spacing between lines
    
    # Wrap text
    wrapped_text = get_wrapped_text(data, 'MySerif', fontSize, page_width * 0.95)
    lines = wrapped_text.split('\n')
    
    # Create a ParagraphStyle
    style = ParagraphStyle(
        name='MyStyle',
        fontName='MySerif',
        fontSize=fontSize,
        leading=line_height,
        alignment=1,  # Center alignment
    )
    
    # Create a Paragraph object
    
    # Create a Paragraph object
    paragraph = Paragraph('<br/>'.join(lines), style)
    
    # Adjust the canvas to start from the bottom
    can.translate(0, 0)
    
    # Create a SimpleDocTemplate
    doc = SimpleDocTemplate(packet, pagesize=(A4[1], A4[0]))
    
    # Build the document with the paragraph
    doc.build([paragraph])
    
    packet.seek(0)
    packet.seek(0)
    new_pdf = PdfReader(packet)
    existing_pdf = PdfReader(input_fn)
    output = PdfWriter()

    for i in range(len(existing_pdf.pages)):
        page = existing_pdf.pages[i]
        if i == 0:
            page.merge_page(new_pdf.pages[0])
        output.add_page(page)

    with open(output_fn, "wb") as outputStream:
        output.write(outputStream)


if __name__ == "__main__":
    writeover(
        "XVIII_KisDurer_eredmenyek.pdf",
        "output2.pdf",
        """A döntőbe jutás feltétele, hoqweqweqwegy a csapat a saját helyszínén győzött (Q), vagy elérte a ponthatárt és iskolájából nem előzte meg egynél több csapat (q). A bejutókat Q és q jelöli
        asdaqwesd"""
    )