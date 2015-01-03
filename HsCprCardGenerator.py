# coding: utf-8
from PyPDF2 import PdfFileReader, PdfFileWriter
import os
import StringIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter


def generate_pdf(
        tc_name="", tc_address="", course_location="", instructor_name_id="",
        issue_date="", expire_date="", test=True, child=True, infant=True,
        student1_name=None, student1_address_1="", student1_address_2="",
        student2_name=None, student2_address_1="", student2_address_2=""):

    #create page1 mask
    packet = StringIO.StringIO()
    # create a new PDF with Reportlab
    can = canvas.Canvas(packet, pagesize=(611.52, 792))
    can.setFont("Helvetica", 10)
    #card 1
    if student1_name is not None:
        can.drawString(363, 741, tc_name)
        can.drawString(363, 716, tc_address)
        can.drawString(363, 692, course_location)
        can.drawString(363, 668, instructor_name_id)
        can.drawString(81, 690, student1_name)
        can.drawString(81, 642, issue_date)
        can.drawString(207, 642, expire_date)
        can.drawString(81,596, student1_name)
        can.drawString(81,576, student1_address_1)
        can.drawString(81,556, student1_address_2)
        if not child:
            can.drawString(128, 655, u"✗")
        if not infant:
            can.drawString(185, 655, u"✗")
        if not test:
            can.drawString(240, 655, u"✗")


    #card 2
    if student2_name is not None:
        can.drawString(363, 329, tc_name)
        can.drawString(363, 307, tc_address)
        can.drawString(363, 283, course_location)
        can.drawString(363, 259, instructor_name_id)
        can.drawString(81, 283, student2_name)
        can.drawString(81, 231, issue_date)
        can.drawString(207, 231, expire_date)
        can.drawString(81,185, student2_name)
        can.drawString(81,169, student2_address_1)
        can.drawString(81,148, student2_address_2)
        if not child:
            can.drawString(128, 246, u"✗")
        if not infant:
            can.drawString(185, 246, u"✗")
        if not test:
            can.drawString(240, 246, u"✗")

    can.save()

    packet.seek(0)
    mask = PdfFileReader(packet)

    return mask

def generate_cards_with_background(pdf):
    dir = os.path.realpath('.')
    #cards
    cards_filename = os.path.join(dir, 'templates','HS_CPR_2_card.pdf')

    cards = PdfFileReader(file(cards_filename, "rb"))

    #merge template with mask

    merged_cards = PdfFileWriter()

    page = cards.getPage(0)
    page.mergePage(pdf.getPage(0))
    merged_cards.addPage(page)

    return merged_cards

def generate_cards_with_no_background(pdf):
    merged_cards = PdfFileWriter()

    page = pdf.getPage(0)
    merged_cards.addPage(page)

    return merged_cards

def main():
    dir = os.path.realpath('.')

    pdf = generate_pdf(
        issue_date="5/2014",
        expire_date="5/2016",
        instructor_name_id="Jane Instructor  12345678901",
        tc_name="Anne Arundel County FD    MD05507",
        tc_address="Millersville, MD 21108",
        course_location="Gambrills, MD",
        student1_name="John Student",
        student1_address_1="123 Anystreet",
        student1_address_2="Crofton, MD 21114",
        student2_name="Jane Student",
        student2_address_1="123 Anystreet",
        student2_address_2="Crofton, MD 21114",
        test=False, infant=False, child=False)

    #merged_cards = generate_cards_with_background(pdf)
    merged_cards = generate_cards_with_no_background(pdf)

    #write pdf to file

    filename = os.path.join(dir, 'test','test_HS_cards.pdf')
    outputStream = file(filename, "wb")
    merged_cards.write(outputStream)
    outputStream.close()

if __name__ == "__main__":
    main()
