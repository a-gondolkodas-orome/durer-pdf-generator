import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

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

def tsv_to_pdf(input_file, output_file):
    # Read the TSV file
    df = pd.read_csv(input_file, sep='\t')
    
    # Create a PDF document
    doc = SimpleDocTemplate(output_file, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
    
    # Calculate available width and height
    available_width = doc.width
    available_height = doc.height
    
    # Calculate column widths (distribute evenly)
    col_width = available_width / len(df.columns)
    
    # Convert the dataframe to a list of lists
    data = [df.columns.tolist()] + df.values.tolist()
    
    # Define fonts
    header_font = 'Helvetica-Bold'
    body_font = 'Helvetica'
    header_font_size = 12
    body_font_size = 10
    
    # Create paragraph styles
    header_style = ParagraphStyle('Header', fontName=header_font, fontSize=header_font_size, leading=header_font_size+2)
    body_style = ParagraphStyle('Body', fontName=body_font, fontSize=body_font_size, leading=body_font_size+2)
    
    # Create table style
    style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 0), (-1, 0), header_font),
        ('FONTSIZE', (0, 0), (-1, 0), header_font_size),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('FONTNAME', (0, 1), (-1, -1), body_font),
        ('FONTSIZE', (0, 1), (-1, -1), body_font_size),
        ('TOPPADDING', (0, 1), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ])
    
    # Wrap text and calculate row heights
    wrapped_data = []
    row_heights = []
    for i, row in enumerate(data):
        wrapped_row = []
        max_height = 0
        for cell in row:
            if i == 0:  # Header row
                wrapped_cell = Paragraph(get_wrapped_text(str(cell), header_font, header_font_size, col_width-12), header_style)
                cell_height = get_text_height(str(cell), header_font, header_font_size, col_width-12)
            else:
                wrapped_cell = Paragraph(get_wrapped_text(str(cell), body_font, body_font_size, col_width-12), body_style)
                cell_height = get_text_height(str(cell), body_font, body_font_size, col_width-12)
            wrapped_row.append(wrapped_cell)
            max_height = max(max_height, cell_height)
        wrapped_data.append(wrapped_row)
        row_heights.append(max_height + 12)  # Add some padding
    
    # Split the table into chunks that fit on one page
    elements = []
    start = 0
    while start < len(wrapped_data) - 1:
        # Always include the header row
        chunk = [wrapped_data[0]]
        chunk_heights = [row_heights[0]]
        chunk_height = chunk_heights[0]
        
        for i, row in enumerate(wrapped_data[start+1:], start=start+1):
            if chunk_height + row_heights[i] <= available_height:
                chunk.append(row)
                chunk_heights.append(row_heights[i])
                chunk_height += row_heights[i]
            else:
                break
        
        # Create a table with the chunk
        t = Table(chunk, colWidths=[col_width] * len(df.columns), rowHeights=chunk_heights)
        t.setStyle(style)
        elements.append(t)
        
        start += len(chunk) - 1  # -1 because we don't want to count the header

    # Build the PDF
    doc.build(elements)

if __name__ == '__main__':
    input_file = 'input.tsv'  # Replace with your TSV file name
    output_file = 'output.pdf'  # Replace with your desired output PDF name
    tsv_to_pdf(input_file, output_file)
    print(f"PDF created successfully: {output_file}")

