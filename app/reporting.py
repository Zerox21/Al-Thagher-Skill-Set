import os
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

def generate_report_pdf(path: str, title_ar: str, lines_ar: list[str]):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    c = canvas.Canvas(path, pagesize=A4)
    width, height = A4
    y = height - 50
    c.setFont("Helvetica", 14)
    c.drawRightString(width - 40, y, title_ar)
    y -= 30
    c.setFont("Helvetica", 11)
    for line in lines_ar:
        if y < 60:
            c.showPage()
            y = height - 50
            c.setFont("Helvetica", 11)
        c.drawRightString(width - 40, y, line)
        y -= 18
    c.save()
