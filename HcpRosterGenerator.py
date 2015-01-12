# coding: utf-8
from PyPDF2 import PdfFileReader, PdfFileWriter, PdfFileMerger
import os
import StringIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import itertools
import csv
from datetime import datetime


def grouper(iterable, n, fillvalue=None):
    "Collect data into fixed-length chunks or blocks"
    # grouper('ABCDEFG', 3, 'x') --> ABC DEF Gxx
    args = [iter(iterable)] * n
    return itertools.izip_longest(fillvalue=fillvalue, *args)

def generate_course_info_page_pdf(class_data, num_students):
    #create page1 mask
    packet = StringIO.StringIO()
    # create a new PDF with Reportlab
    can = canvas.Canvas(packet, pagesize=(792, 612))
    can.setFont("Helvetica", 10)

    if (class_data['options']['New']):
        can.drawString(58, 428, u"✗")

    if (class_data['options']['Renewal']):
        can.drawString(58, 416, u"✗")

    if (class_data['options']['Instructor']):
        can.drawString(58, 404, u"✗")

    if (class_data['options']['Provider']):
        can.drawString(58, 392, u"✗")

    can.drawString(495, 426, class_data['curr_instructor']['instructor_name'])
    can.drawString(519, 403, class_data['curr_instructor']['instructor_renewal_date'])
    can.drawString(493, 389, class_data['curr_instructor']['training_center_id'])
    can.drawString(512, 378, class_data['curr_instructor']['training_center_name'])
    can.drawString(510, 366, '') #training site name
    can.drawString(493, 354, class_data['class_location'])
    can.drawString(493, 341, '') #address

    can.drawString(165, 283, class_data['class_date'].strftime("%m/%d/%y"))
    can.drawString(378, 283, class_data['class_date'].strftime("%m/%d/%y"))
    can.drawString(614, 283, "4")
    can.drawString(153, 259, str(num_students))
    can.drawString(381, 259, class_data['student_manikin_ratio'])
    can.drawString(581, 259, class_data['card_issue_date'].strftime("%m/%y"))

    can.save()

    packet.seek(0)
    mask = PdfFileReader(packet)

    dir = os.path.realpath('.')
    #cards
    roster_filename = os.path.join(dir, 'pdf_templates','HCP_roster.pdf')

    roster = PdfFileReader(file(roster_filename, "rb"))

    #merge template with mask

    merged_roster = PdfFileWriter()

    page = roster.getPage(0)
    page.mergePage(mask.getPage(0))
    merged_roster.addPage(page)

    return merged_roster

def generate_student_page_pdf(students, instructor_name, course_date):
    '''
    students = [{name, street_address, city_state},...]
    '''

    #create page1 mask
    packet = StringIO.StringIO()
    # create a new PDF with Reportlab
    can = canvas.Canvas(packet, pagesize=(792, 612))
    can.setFont("Helvetica", 10)

    can.drawString(86, 571, course_date.strftime("%m/%d/%y"))
    can.drawString(238, 571, "Heartsaver CPR AED")
    can.drawString(503, 571, instructor_name)


    #iterate through students
    for i, next_student in enumerate(students):
        if next_student != None:
            offset = i * 46.5
            can.drawString(79, 480-offset, next_student['name'])
            can.drawString(306, 480-offset, next_student['street_address'])
            can.drawString(306, 464-offset, next_student['city_state'])
            can.drawString(540, 479-offset, 'Complete')

    can.save()

    packet.seek(0)
    mask = PdfFileReader(packet)

    dir = os.path.realpath('.')
    #cards
    roster_filename = os.path.join(dir, 'pdf_templates','HCP_roster.pdf')

    roster = PdfFileReader(file(roster_filename, "rb"))

    #merge template with mask

    merged_roster = PdfFileWriter()

    page = roster.getPage(1)
    page.mergePage(mask.getPage(0))
    merged_roster.addPage(page)

    return merged_roster

def generate_pdf(class_data):
    '''
    Arguments:
    class_data: Dictionary with the following keys
        student_manikin_ratio
        students: [{name, street_address, city_state}],
        curr_instructor: {training_center_id,
                            training_center_address,
                            instructor_id, training_center_name,
                            instructor_renewal_date, instructor_name,
                            _id: ObjectId},
        curr_course_type_id,
        curr_course_type,
        class_date: datetime,
        _id: ObjectId,
        class_location,
        options: {Infants, Written, Child}
    '''

    course_info_page = generate_course_info_page_pdf(class_data, len(class_data['students']))

    ci_packet = StringIO.StringIO()

    course_info_page.write(ci_packet)
    ci_packet.seek(0)

    merged_roster = PdfFileMerger()

    merged_roster.append(PdfFileReader(ci_packet))

    #create student pages

    for studentSubGroup in grouper(class_data['students'], 10):
        next_roster_page = generate_student_page_pdf(studentSubGroup, class_data['curr_instructor']['instructor_name'], class_data['class_date'])
        nrp_packet = StringIO.StringIO()
        next_roster_page.write(nrp_packet)
        nrp_packet.seek(0)
        merged_roster.append(PdfFileReader(nrp_packet))


    return merged_roster

def main():
    class_data = {'student_manikin_ratio':"2:1",
    'students': [{'name':'john doe', 'street_address':'12345 some street', 'city_state':'some city'}],
    'curr_instructor': {'training_center_id':'123455',
                        'training_center_address':'maryland',
                        'instructor_id':'1234',
                        'training_center_name':'some TC',
                        'instructor_renewal_date':'5/11/2014',
                        'instructor_name':'Someone',
                        },
    'curr_course_type_id':1,
    'curr_course_type':"Heartsaver CPR",
    'class_date': datetime.today(),
    'card_issue_date':datetime.today(),
    'class_location':"Crofton,MD",
    'options': {'New':True, 'Renewal':True, 'Instructor':True,'Provider':True}}

    pdf = generate_pdf(class_data)
    #write combined pdf to file
    dir = os.path.realpath('.')
    filename = os.path.join(dir, 'test','test_HCP_roster.pdf')
    outputStream = file(filename, "wb")
    pdf.write(outputStream)
    outputStream.close()

if __name__ == "__main__":
    main()
