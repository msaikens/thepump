import os
from flask import Flask, request, render_template, send_from_directory, redirect
import json
from pymongo import MongoClient
from bson.objectid import ObjectId
from datetime import datetime
import pymongo


MONGODB_URI = os.environ['MONGOLAB_URI']

# initialization
app = Flask(__name__)
app.config.from_object(__name__)

if os.environ['DEBUG'] == 'true':
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
    return render_template('index.html')

@app.route("/class/new/")
def new_class():
    # create blank class
    class_data={}

    class_data['students'] = {}
    #TODO: pull options from lookup table
    class_data['options'] = {'Child':'false',"Infants":'false','Written':'false'}
    class_data['class_date'] = datetime.today()
    class_data['_id'] = 0
    class_data['curr_instructor'] = 0
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

    return render_template('showclass.html', class_data = class_data)

@app.route("/class/<class_id>/", methods=['POST'])
def update_class(class_id):
    #update class details, then show class

    edit = request.args.get('edit', 'false')

    #map request data into our data object
    class_data={}

    try:
        class_data['curr_instructor']=request.form['curr_instructor']

        #convert date to datetime
        try:
            class_data['class_date'] = datetime.strptime(request.form['class_date'], '%m/%d/%Y')
        except ValueError:
            error = True

        if class_id != '0':
            class_data['_id']=ObjectId(class_id)
        class_data['curr_course_type']=request.form['course_type']

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

    class_data['students'] ={}
    num_students = int(request.form['num_students'])
    for x in range(num_students):
        next_student_key = 'student_'+str(x)
        next_student_name_key = next_student_key+'-name'
        next_student_address_key = next_student_key+'-street_address'
        next_student_city_key = next_student_key+'-city_state'
        try:
            class_data['students'][next_student_key] = {}
            class_data['students'][next_student_key]['name'] = request.form[next_student_name_key]
            class_data['students'][next_student_key]['street_address'] = request.form[next_student_address_key]
            class_data['students'][next_student_key]['city_state'] = request.form[next_student_city_key]
        except KeyError:
            error = True

    #see if there's a new student
    try:
        new_student_name = request.form['new_student-name']
        if new_student_name != '':
            new_student_key = 'student_'+str(len(class_data['students']))
            class_data['students'][new_student_key] = {}
            class_data['students'][new_student_key]['name'] = request.form['new_student-name']
            class_data['students'][new_student_key]['street_address'] = request.form['new_student-street_address']
            class_data['students'][new_student_key]['city_state'] = request.form['new_student-city_state']

    except KeyError:
        error = True


    #persist to datastore
    client = MongoClient(MONGODB_URI)
    db = client.get_default_database()
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

    return render_template('showclass.html', class_data="nop")


def render_edit_class(class_data, request_data):
    #TODO: pull real data
    instructors = [[12345, "J. Richmond"],[567789, "C. Richmond"],[145643, "J. Tobin"]]
    course_types = [["Heartsaver CPR","Heartsaver CPR"],["Heartsaver First Aid","Heartsaver First Aid"],["Heartsaver CPR/First Aid","Heartsaver CPR/First Aid"],["Healthcare Provider","Healthcare Provider"]]
    return render_template('editclass.html',class_data = class_data, instructors=instructors, course_types=course_types, request_data=request_data)


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
        upcoming_classes.append({'course_type':course['curr_course_type'],'course_date':course['class_date'],'instructor':course['curr_instructor']})
    client.close()

    return render_template('class.html', class_list=upcoming_classes, page_name="Upcoming Classes", page_id="upcoming")

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
        upcoming_classes.append({'course_type':course['curr_course_type'],'course_date':course['class_date'],'instructor':course['curr_instructor']})
    client.close()

    return render_template('class.html', class_list=upcoming_classes, page_name="Historic Classes", page_id="historic")

@app.route("/instructor/")
def instructors():
    #TODO: pull upcoming classes from database
    instructors = [{"_id":12345,"name":"J. Richmond"},{"_id":567789, "name":"C. Richmond"},{"_id":145643, "name":"J. Tobin"}]
    return render_template('instructors.html', instructors=instructors)

@app.route("/instructor/<instructor_id>/", methods=['GET'])
def view_instructor(instructor_id):
    edit = request.args.get('edit', 'false')

    instructor= {"_id":12345,"instructor_name":"J. Richmond","instructor_id":"1234566433",'instructor_renewal_date':"5/1/2015","training_center_name":"Anne Arundel County FD","training_center_id":"MD123445","training_center_address":"100 Annapolis Road"}

    if edit == 'true':
        return render_template('edit_instructor.html', instructor=instructor)

    return render_template('view_instructor.html', instructor=instructor)

# launch
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
