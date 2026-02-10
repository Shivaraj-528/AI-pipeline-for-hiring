# utils/text_to_pdf.py

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.enums import TA_LEFT, TA_CENTER


def text_to_pdf(text_file_path, pdf_output_path):
    """
    Convert a text file to PDF format.
    """
    # Read text file
    with open(text_file_path, 'r') as f:
        content = f.read()
    
    # Create PDF
    doc = SimpleDocTemplate(pdf_output_path, pagesize=letter)
    story = []
    
    # Styles
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        textColor='#000000',
        spaceAfter=12,
        alignment=TA_CENTER
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=12,
        textColor='#000000',
        spaceAfter=6,
        spaceBefore=12
    )
    
    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['BodyText'],
        fontSize=10,
        textColor='#000000',
        spaceAfter=6,
        alignment=TA_LEFT
    )
    
    # Parse content
    lines = content.split('\n')
    
    for line in lines:
        line = line.strip()
        
        if not line:
            story.append(Spacer(1, 0.1 * inch))
            continue
        
        # Detect headings (all caps or specific keywords)
        if line.isupper() or line in ['Professional Summary', 'Technical Skills', 'Projects', 'Education']:
            story.append(Paragraph(line, heading_style))
        # First line is title
        elif lines.index(line + '\n') == 0 or 'MERN Stack Developer' in line:
            story.append(Paragraph(line, title_style))
        else:
            # Escape HTML special characters
            line = line.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            story.append(Paragraph(line, body_style))
    
    # Build PDF
    doc.build(story)
    print(f"✅ PDF created: {pdf_output_path}")


if __name__ == "__main__":
    import sys
    if len(sys.argv) == 3:
        text_to_pdf(sys.argv[1], sys.argv[2])
    else:
        print("Usage: python text_to_pdf.py <input.txt> <output.pdf>")
