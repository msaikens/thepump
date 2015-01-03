# coding: utf-8
from PyPDF2 import PdfFileReader, PdfFileWriter, PdfFileMerger
import os
import StringIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import itertools
import csv

def grouper(iterable, n, fillvalue=None):
    "Collect data into fixed-length chunks or blocks"
    # grouper('ABCDEFG', 3, 'x') --> ABC DEF Gxx
    args = [iter(iterable)] * n
    return itertools.izip_longest(fillvalue=fillvalue, *args)

def generate_course_info_page_pdf(course_info, num_students):
    #create page1 mask
    packet = StringIO.StringIO()
    # create a new PDF with Reportlab
    can = canvas.Canvas(packet, pagesize=(792, 612))
    can.setFont("Helvetica", 10)

    can.drawString(58, 428, u"✗")
    if (course_info['child_cpr'] == 'yes'):
        can.drawString(76, 415, u"✗")
    if (course_info['infant_cpr'] == 'yes'):
        can.drawString(171, 415, u"✗")
    if (course_info['written_test'] == 'yes'):
        can.drawString(243, 415, u"✗")

    can.drawString(495, 426, course_info['instructor_name'])
    can.drawString(519, 403, u"✗")
    can.drawString(512, 389, course_info['instructor_renewal_date'])
    can.drawString(493, 378, course_info['training_center_name'])
    can.drawString(510, 366, course_info['training_center_id'])
    can.drawString(493, 341, course_info['course_location'])

    can.drawString(165, 268, course_info['course_date'])
    can.drawString(378, 268, course_info['course_date'])
    can.drawString(614, 268, "4")
    can.drawString(153, 244, str(num_students))
    can.drawString(381, 244, course_info['student_manikin_ratio'])
    can.drawString(581, 244, course_info['card_issue_date'])

    can.save()

    packet.seek(0)
    mask = PdfFileReader(packet)

    dir = os.path.realpath('.')
    #cards
    roster_filename = os.path.join(dir, 'templates','HS_roster.pdf')

    roster = PdfFileReader(file(roster_filename, "rb"))

    #merge template with mask

    merged_roster = PdfFileWriter()

    page = roster.getPage(0)
    page.mergePage(mask.getPage(0))
    merged_roster.addPage(page)

    return merged_roster

def generate_student_page_pdf(students, instructor_name, course_date):
    #create page1 mask
    packet = StringIO.StringIO()
    # create a new PDF with Reportlab
    can = canvas.Canvas(packet, pagesize=(792, 612))
    can.setFont("Helvetica", 10)

    can.drawString(86, 571, course_date)
    can.drawString(238, 571, "Heartsaver CPR AED")
    can.drawString(503, 571, instructor_name)


    #iterate through students
    for i, next_student in enumerate(students):
        if next_student != None:
            offset = i * 46.5
            can.drawString(79, 480-offset, next_student['student_name'])
            can.drawString(306, 480-offset, next_student['student_address_1'])
            can.drawString(306, 464-offset, next_student['student_address_2'])
            can.drawString(540, 479-offset, 'Complete')

    can.save()

    packet.seek(0)
    mask = PdfFileReader(packet)

    dir = os.path.realpath('.')
    #cards
    roster_filename = os.path.join(dir, 'templates','HS_roster.pdf')

    roster = PdfFileReader(file(roster_filename, "rb"))

    #merge template with mask

    merged_roster = PdfFileWriter()

    page = roster.getPage(1)
    page.mergePage(mask.getPage(0))
    merged_roster.addPage(page)

    return merged_roster

def generate_pdf(course_info, students):
    '''
    Arguments:
    course_info: Dictionary with the following keys
        instructor_name,instructor_id,training_center_name, training_center_id,
        training_center_address,course_location,course_date,card_issue_date,
        card_expire_date,written_test,child_cpr,infant_cpr
    students: List of dictionarys with the following keys
        student_name,student_address_1,student_address_2
    '''

    course_info_page = generate_course_info_page_pdf(course_info, len(students))

    ci_packet = StringIO.StringIO()

    course_info_page.write(ci_packet)
    ci_packet.seek(0)

    merged_roster = PdfFileMerger()

    merged_roster.append(PdfFileReader(ci_packet))

    #TODO: create student pages

    for studentSubGroup in grouper(students, 10):
        next_roster_page = generate_student_page_pdf(studentSubGroup, course_info['instructor_name'], course_info['course_date'])
        nrp_packet = StringIO.StringIO()
        next_roster_page.write(nrp_packet)
        nrp_packet.seek(0)
        merged_roster.append(PdfFileReader(nrp_packet))


    return merged_roster


def main():

    dir = os.path.realpath('.')
    filename = os.path.join(dir, 'test','students.csv')
    students = []
    with open(filename, 'rb') as csvfile:
        students_csv = csv.DictReader(csvfile)
        for row in students_csv:
            if(row["student_name"] != ''):
                students.append(row)

    course_info = {}
    course_info_filename = os.path.join(dir, 'test', 'HS_CPR_course_info.csv')
    with open (course_info_filename, 'rb') as course_info_csv:
        course_info_csv = csv.DictReader(course_info_csv)
        for row in course_info_csv:
            course_info = row

    pdf = generate_pdf(course_info, students)

    #write pdf to file
    filename = os.path.join(dir, 'test','test_HS_roster.pdf')
    outputStream = file(filename, "wb")
    pdf.write(outputStream)
    outputStream.close()

if __name__ == "__main__":
    main()
