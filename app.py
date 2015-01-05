import os
from flask import Flask, request, render_template, send_from_directory, redirect, make_response
import json
from pymongo import MongoClient
from bson.objectid import ObjectId
from datetime import datetime
import pymongo
import HsCprCardGenerator
import HsCprSkillsGenerator
import HsCprRosterGenerator
import StringIO
from PyPDF2 import PdfFileMerger, PdfFileReader
import itertools



MONGODB_URI = os.environ['MONGOLAB_URI']

COURSE_TYPES = {1:"Heartsaver CPR",2:"Heartsaver First Aid",3:"Heartsaver CPR/First Aid",4:"Healthcare Provider"}

DEBUG = os.environ.get('DEBUG', False)

# initialization
app = Flask(__name__)
app.config.from_object(__name__)

if DEBUG:
    app.debug = True

# controllers
@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'ico/favicon.ico')

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.route("/")
def index():
    return render_template('index.html', debug=DEBUG)

@app.route("/class/new/")
def new_class():
    # create blank class
    class_data={}

    class_data['students'] = []
    #TODO: pull options from lookup table
    class_data['class_location'] = ''
    class_data['student_manikin_ratio'] = ''
    class_data['options'] = {'Child':False,"Infants":False,'Written':False}
    class_data['class_date'] = datetime.today()
    class_data['_id'] = 0
    class_data['curr_instructor'] = {}
    class_data['curr_course_type'] = 0
    return render_edit_class(class_data, '')

@app.route("/class/<class_id>/", methods=['GET'])
def show_class(class_id):

    #redirect if someone cancels creating a new class
    if class_id == '0':
        return redirect('/class/', code=303)

    # pull class details for selected class
    client = MongoClient(MONGODB_URI)
    db = client.get_default_database()
    courses = db['courses']
    class_data = courses.find_one({"_id": ObjectId(class_id)})
    client.close()

    edit = request.args.get('edit', 'false')

    if edit == 'true':
        return render_edit_class(class_data, '')

    return render_template('showclass.html', class_data = class_data, debug=DEBUG)

@app.route("/class/<class_id>/", methods=['POST'])
def update_class(class_id):
    #update class details, then show class

    edit = request.args.get('edit', 'false')

    #open up database early so that we can pull instructor details
    client = MongoClient(MONGODB_URI)
    db = client.get_default_database()

    #map request data into our data object
    class_data={}

    try:
        instructors = db['instructors']
        instructor = instructors.find_one({"_id": ObjectId(request.form['curr_instructor'])})

        class_data['curr_instructor']=instructor

        class_data['class_location'] = request.form['class_location']
        class_data['student_manikin_ratio'] = request.form['student_manikin_ratio']

        #convert date to datetime
        try:
            class_data['class_date'] = datetime.strptime(request.form['class_date'], '%m/%d/%Y')
        except ValueError:
            #handle Chrome (HTML5 date form field) date formatting
            class_data['class_date'] = datetime.strptime(request.form['class_date'], '%Y-%m-%d')
            #error = True

        if class_id != '0':
            class_data['_id']=ObjectId(class_id)

        class_data['curr_course_type_id']=request.form['course_type']
        class_data['curr_course_type']=COURSE_TYPES[int(class_data['curr_course_type_id'])]

        #pull options. #TODO: pull available options from lookup table
        class_data['options'] = {}

        if 'Child' in request.form:
            class_data['options']['Child'] = True
        else:
            class_data['options']['Child'] = False

        if 'Infants' in request.form:
            class_data['options']['Infants'] = True
        else:
            class_data['options']['Infants'] = False

        if 'Written' in request.form:
            class_data['options']['Written'] = True
        else:
            class_data['options']['Written'] = False

    except KeyError:
        #todo: something here
        error = True

    class_data['students'] = []
    num_students = int(request.form['num_students'])
    for x in range(num_students):
        next_student_key = 'student_'+str(x)
        next_student_name_key = next_student_key+'-name'
        next_student_address_key = next_student_key+'-street_address'
        next_student_city_key = next_student_key+'-city_state'
        try:
            student = {}
            student['name'] = request.form[next_student_name_key]
            student['street_address'] = request.form[next_student_address_key]
            student['city_state'] = request.form[next_student_city_key]

            class_data['students'].append(student)

        except KeyError:
            error = True

    #see if there's a new student
    try:
        new_student_name = request.form['new_student-name']
        if new_student_name != '':
            student = {}
            student['name'] = request.form['new_student-name']
            student['street_address'] = request.form['new_student-street_address']
            student['city_state'] = request.form['new_student-city_state']

            class_data['students'].append(student)


    except KeyError:
        error = True


    #persist to datastore

    courses = db['courses']
    #if new class, create new record
    course_id = courses.save(class_data)
    class_data['_id'] = course_id

    client.close()

    if edit == 'true':
        if DEBUG:
            request_data = request.form
        else:
            request_data = ' '

        if class_id == '0':
            return redirect('/class/'+str(course_id)+'/', code=303)
        else:
            return render_edit_class(class_data, request_data)

    return render_template('showclass.html', class_data=class_data)


def render_edit_class(class_data, request_data):
    #TODO: pull real data
    client = MongoClient(MONGODB_URI)
    db = client.get_default_database()
    instructors_db = db['instructors']
    instructors_list = []
    instructors = list(instructors_db.find())
    for next_instructor in instructors:
        instructors_list.append({"_id":str(next_instructor['_id']),"name":next_instructor['instructor_name']})
    client.close()

    return render_template('editclass.html',class_data = class_data, instructors=instructors_list, course_types=COURSE_TYPES, request_data=request_data, debug=DEBUG)

@app.route("/class/<class_id>/skillsheets/")
def gen_class_skillsheets(class_id):
    # pull class details for selected class
    client = MongoClient(MONGODB_URI)
    db = client.get_default_database()
    courses = db['courses']
    class_data = courses.find_one({"_id": ObjectId(class_id)})
    client.close()

    output = StringIO.StringIO()
    skillsheets = []

    for row in class_data['students']:
        if(row["name"] != ''):
            next_skillsheet = HsCprSkillsGenerator.generate_pdf(row["name"],
                class_data["class_date"].strftime("%m/%d/%y"), class_data['curr_instructor']['instructor_name'],
                adult=True, child=class_data['options']['Child'], infant=class_data['options']['Infants'])
            ss_packet = StringIO.StringIO()
            next_skillsheet.write(ss_packet)
            skillsheets.append(ss_packet)

    merged_skillsheets = PdfFileMerger()
    for next_skillsheet in skillsheets:
        next_skillsheet.seek(0)
        merged_skillsheets.append(PdfFileReader(next_skillsheet))

    merged_skillsheets.write(output)
    pdf_out = output.getvalue()
    output.close()


    response = make_response(pdf_out)
    #TODO: better filenames
    response.headers['Content-Disposition'] = "attachment; filename='skillsheets.pdf"
    response.mimetype = 'application/pdf'
    return response

@app.route("/class/<class_id>/roster/")
def gen_class_roster(class_id):
    # pull class details for selected class
    client = MongoClient(MONGODB_URI)
    db = client.get_default_database()
    courses = db['courses']
    class_data = courses.find_one({"_id": ObjectId(class_id)})
    if 'card_issue_date' not in class_data:
        today = datetime.now()
        class_data['card_issue_date'] = today
        class_data['card_expire_date'] = today.replace(year=today.year + 2)
        courses.save(class_data)
    client.close()

    roster = HsCprRosterGenerator.generate_pdf(class_data)

    output = StringIO.StringIO()
    roster.write(output)
    pdf_out = output.getvalue()
    output.close()

    response = make_response(pdf_out)
    #TODO: better filenames
    response.headers['Content-Disposition'] = "attachment; filename='roster.pdf"
    response.mimetype = 'application/pdf'
    return response

@app.route("/class/<class_id>/cards/")
def gen_class_cards(class_id):
    # pull class details for selected class
    client = MongoClient(MONGODB_URI)
    db = client.get_default_database()
    courses = db['courses']
    class_data = courses.find_one({"_id": ObjectId(class_id)})
    #set card issue date to today
    today = datetime.now()
    class_data['card_issue_date'] = today
    class_data['card_expire_date'] = today.replace(year=today.year + 2)
    courses.save(class_data)
    client.close()

    print_cards = []
    for student1, student2 in grouper(class_data['students'], 2):
        if(student2 != None):
            next_card_mask = HsCprCardGenerator.generate_pdf(
                tc_name=class_data['curr_instructor']["training_center_name"]+" "+class_data['curr_instructor']["training_center_id"],
                tc_address=class_data['curr_instructor']["training_center_address"],
                course_location=class_data["class_location"],
                instructor_name_id=class_data['curr_instructor']["instructor_name"]+" "+class_data['curr_instructor']["instructor_id"],
                issue_date=class_data["card_issue_date"].strftime("%m/%y"),
                expire_date=class_data["card_expire_date"].strftime("%m/%y"),
                test=class_data['options']['Written'], child=class_data['options']['Child'], infant=class_data['options']['Infants'],
                student1_name=student1["name"],
                student1_address_1=student1["street_address"],
                student1_address_2=student1["city_state"],
                student2_name=student2["name"],
                student2_address_1=student2["street_address"],
                student2_address_2=student2["city_state"])
        else:
            next_card_mask = HsCprCardGenerator.generate_pdf(
                tc_name=class_data['curr_instructor']["training_center_name"]+" "+class_data['curr_instructor']["training_center_id"],
                tc_address=class_data['curr_instructor']["training_center_address"],
                course_location=class_data["class_location"],
                instructor_name_id=class_data['curr_instructor']["instructor_name"]+" "+class_data['curr_instructor']["instructor_id"],
                issue_date=class_data["card_issue_date"].strftime("%m/%y"),
                expire_date=class_data["card_expire_date"].strftime("%m/%y"),
                test=class_data['options']['Written'], child=class_data['options']['Child'], infant=class_data['options']['Infants'],
                student1_name=student1["name"],
                student1_address_1=student1["street_address"],
                student1_address_2=student1["city_state"])

        print_card = HsCprCardGenerator.generate_cards_with_no_background(next_card_mask)

        pc_packet = StringIO.StringIO()
        print_card.write(pc_packet)
        print_cards.append(pc_packet)

    merged_print_cards = PdfFileMerger()
    for next_print_card in print_cards:
        next_print_card.seek(0)
        merged_print_cards.append(PdfFileReader(next_print_card))


    output = StringIO.StringIO()
    merged_print_cards.write(output)
    pdf_out = output.getvalue()
    output.close()

    response = make_response(pdf_out)
    #TODO: better filenames
    response.headers['Content-Disposition'] = "attachment; filename='cards.pdf"
    response.mimetype = 'application/pdf'
    return response


@app.route("/class/")
def upcoming():
    #pull upcoming classes from database
    client = MongoClient(MONGODB_URI)
    db = client.get_default_database()
    courses = db['courses']
    upcoming_classes = []
    courses.ensure_index("class_date", pymongo.DESCENDING)
    sorted_classes = list(courses.find({"class_date":{"$gte":datetime.now()}}).sort("class_date",pymongo.DESCENDING))
    for course in sorted_classes:
        upcoming_classes.append({'_id':course['_id'],'course_type':course['curr_course_type'],'course_date':course['class_date'],'instructor':course['curr_instructor']['instructor_name']})
    client.close()

    return render_template('class.html', class_list=upcoming_classes, page_name="Upcoming Classes", page_id="upcoming", debug=DEBUG)

@app.route("/historic/")
def historic():
    #pull upcoming classes from database
    client = MongoClient(MONGODB_URI)
    db = client.get_default_database()
    courses = db['courses']
    upcoming_classes = []
    courses.ensure_index("class_date", pymongo.DESCENDING)
    sorted_classes = list(courses.find({"class_date":{"$lt":datetime.now()}}).sort("class_date",pymongo.DESCENDING))
    for course in sorted_classes:
        upcoming_classes.append({'_id':course['_id'],'course_type':course['curr_course_type'],'course_date':course['class_date'],'instructor':course['curr_instructor']['instructor_name']})
    client.close()

    return render_template('class.html', class_list=upcoming_classes, page_name="Historic Classes", page_id="historic", debug=DEBUG)

@app.route("/instructor/")
def instructors():
    #pull instructors from database

    client = MongoClient(MONGODB_URI)
    db = client.get_default_database()
    instructors_db = db['instructors']
    instructors_list = []
    instructors = list(instructors_db.find())
    for next_instructor in instructors:
        instructors_list.append({"_id":str(next_instructor['_id']),"name":next_instructor['instructor_name']})
    client.close()

    return render_template('instructors.html', instructors=instructors_list, debug=DEBUG)

@app.route("/instructor/new/")
def new_instructor():

    #default instructor - important thing here is that the _id is 0
    instructor= {"_id":0,
        "instructor_name":"",
        "instructor_id":"",
        'instructor_renewal_date':"",
        "training_center_name":"",
        "training_center_id":"",
        "training_center_address":""}

    return render_template('edit_instructor.html', instructor=instructor, debug=DEBUG)

@app.route("/instructor/<instructor_id>/", methods=['GET'])
def view_instructor(instructor_id):
    edit = request.args.get('edit', 'false')
    #redirect if someone cancels creating a new instructor
    if instructor_id == '0':
        return redirect('/instructor/', code=301)

    # pull class details for selected class
    client = MongoClient(MONGODB_URI)
    db = client.get_default_database()
    instructors = db['instructors']
    instructor = instructors.find_one({"_id": ObjectId(instructor_id)})
    client.close()


    if edit == 'true':
        return render_template('edit_instructor.html', instructor=instructor, debug=DEBUG)

    return render_template('view_instructor.html', instructor=instructor, debug=DEBUG)

@app.route("/instructor/<instructor_id>/", methods=['POST'])
def update_instructor(instructor_id):
    edit = request.args.get('edit', 'false')

    #map request data into our data object
    instructor={}
    try:
        if instructor_id != '0':
            instructor['_id']=ObjectId(instructor_id)

        instructor['instructor_name']=request.form['instructor_name']
        instructor['instructor_id']=request.form['instructor_id']
        instructor['instructor_renewal_date']=request.form['instructor_renewal_date']
        instructor['training_center_name']=request.form['training_center_name']
        instructor['training_center_id']=request.form['training_center_id']
        instructor['training_center_address']=request.form['training_center_address']

    except KeyError:
        error = True

    #persist to datastore
    client = MongoClient(MONGODB_URI)
    db = client.get_default_database()
    instructors = db['instructors']
    #if new class, create new record
    real_instructor_id = instructors.save(instructor)
    instructor['_id'] = real_instructor_id

    client.close()

    if edit == 'true':
        if instructor_id == '0':
            return redirect('/instructor/'+str(real_instructor_id)+'/', code=303)
        else:
            return render_template('edit_instructor.html', instructor=instructor, debug=DEBUG)

    return render_template('view_instructor.html', instructor=instructor, debug=DEBUG)

#helper class
def grouper(iterable, n, fillvalue=None):
    "Collect data into fixed-length chunks or blocks"
    # grouper('ABCDEFG', 3, 'x') --> ABC DEF Gxx
    args = [iter(iterable)] * n
    return itertools.izip_longest(fillvalue=fillvalue, *args)

# launch
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
