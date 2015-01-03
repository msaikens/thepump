import os
from flask import Flask, request, render_template, send_from_directory, redirect
import json
from pymongo import MongoClient
from bson.objectid import ObjectId
from datetime import datetime
import pymongo


MONGODB_URI = os.environ['MONGOLAB_URI']

COURSE_TYPES = {1:"Heartsaver CPR",2:"Heartsaver First Aid",3:"Heartsaver CPR/First Aid",4:"Healthcare Provider"}

DEBUG = (os.environ['DEBUG'] == 'true')

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

    class_data['students'] = {}
    #TODO: pull options from lookup table
    class_data['options'] = {'Child':'false',"Infants":'false','Written':'false'}
    class_data['class_date'] = datetime.today()
    class_data['_id'] = 0
    class_data['curr_instructor'] = {}
    class_data['curr_course_type'] = 0
    return render_edit_class(class_data, '')

@app.route("/class/<class_id>/", methods=['GET'])
def show_class(class_id):

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
            class_data['options']['Child'] = 'true'
        else:
            class_data['options']['Child'] = 'false'

        if 'Infants' in request.form:
            class_data['options']['Infants'] = 'true'
        else:
            class_data['options']['Infants'] = 'false'

        if 'Written' in request.form:
            class_data['options']['Written'] = 'true'
        else:
            class_data['options']['Written'] = 'false'

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
        if os.environ['DEBUG'] == 'true':
            request_data = request.form
        else:
            request_data = ''

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


# launch
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
