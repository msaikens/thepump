# coding: utf-8
from PyPDF2 import PdfFileReader, PdfFileWriter
import os
import StringIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter


def generate_pdf(student_name="",test_date="",instructor_name=""):

    #create page1 mask
    packet = StringIO.StringIO()
    # create a new PDF with Reportlab
    can = canvas.Canvas(packet, pagesize=(605.8, 785.86))


    can.drawString(113, 665, student_name)
    can.drawString(450, 665, test_date)
    can.drawString(146, 71, instructor_name)
    can.drawString(84, 55, test_date)

    #pass adult CPR and AED
    can.ellipse(298,654, 325,642)
    can.ellipse(298,638, 325,626)

    #check some boxes

    can.drawString(516, 550, u"✓")
    can.drawString(516, 533, u"✓")
    can.drawString(516, 515, u"✓")
    can.drawString(540, 483, u"✓")
    can.drawString(540, 457, u"<18")
    can.drawString(540, 435, u"✓")
    can.drawString(540, 416, u"✓")
    can.drawString(540, 397, u"✓")
    can.drawString(516, 349, u"✓")
    can.drawString(516, 330, u"✓")
    can.drawString(516, 314, u"✓")
    can.drawString(516, 296, u"✓")
    can.drawString(494, 239, u"✓")
    can.drawString(538, 239, u"✓")
    can.drawString(494, 219, u"✓")
    can.drawString(538, 219, u"✓")

    #next page!
    can.showPage()

    can.drawString(113, 662, student_name)
    can.drawString(450, 662, test_date)
    can.drawString(146, 79, instructor_name)
    can.drawString(84, 63, test_date)

    #pass adult CPR and AED
    can.ellipse(346,654, 373,642)
    can.ellipse(346,631, 373,619)
    can.ellipse(346,619, 373,607)

    #check some boxes

    can.drawString(516, 538, u"✓")
    can.drawString(516, 519, u"✓")
    can.drawString(516, 505, u"✓")
    can.drawString(540, 476, u"✓")
    can.drawString(540, 452, u"<18")
    can.drawString(540, 433, u"✓")
    can.drawString(540, 411, u"✓")
    can.drawString(540, 397, u"✓")
    can.drawString(516, 344, u"✓")
    can.drawString(494, 289, u"✓")
    can.drawString(538, 289, u"✓")

    can.drawString(494, 239, u"<9")
    can.drawString(538, 239, u"<9")

    can.save()

    #move to the beginning of the StringIO buffer
    packet.seek(0)
    mask = PdfFileReader(packet)

    #open up template
    output = PdfFileWriter()
    dir = os.path.realpath('.')
    as_filename = os.path.join(dir, 'pdf_templates','HCP_adult_skills.pdf')
    adult_skills_template = PdfFileReader(file(as_filename, "rb"))
    is_filename = os.path.join(dir, 'pdf_templates','HCP_infant_skills.pdf')
    infant_skills_template = PdfFileReader(file(is_filename, "rb"))

    #merge template with mask

    page = adult_skills_template.getPage(0)
    page.mergePage(mask.getPage(0))
    output.addPage(page)
    page2 = infant_skills_template.getPage(0)
    page2.mergePage(mask.getPage(1))
    output.addPage(page2)

    return output




def main():
    pdf = generate_pdf("John Student", "5/15/15", "Jane Instructor")
    #write pdf to file

    dir = os.path.realpath('.')
    filename = os.path.join(dir, 'test','test_HCP_skillsheet.pdf')
    outputStream = file(filename, "wb")
    pdf.write(outputStream)
    outputStream.close()

if __name__ == "__main__":
    main()
