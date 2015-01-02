import os
from flask import Flask, request, render_template, send_from_directory, redirect
import json
from pymongo import MongoClient
from bson.objectid import ObjectId

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
    class_data['class_date'] = ""
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
    #TODO: update class details, then show class

    edit = request.args.get('edit', 'false')

    #map request data into our data object
    class_data={}

    try:
        class_data['curr_instructor']=request.form['curr_instructor']
        class_data['class_date']=request.form['class_date']
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
    course_types = [[1,"Heartsaver CPR"],[2,"Heartsaver First Aid"],[3,"Heartsaver CPR/First Aid"],[4,"Healthcare Provider"]]
    return render_template('editclass.html',class_data = class_data, instructors=instructors, course_types=course_types, request_data=request_data)


@app.route("/class/")
def upcoming():
    #TODO: pull upcoming classes from database
    client = MongoClient(MONGODB_URI)
    db = client.get_default_database()
    courses = db['courses']
    upcoming_classes = {}
    for course in courses.find():
        upcoming_classes[str(course['_id'])] = {'course_type':course['curr_course_type'],'course_date':course['class_date'],'instructor':course['curr_instructor']}
    client.close()

    return render_template('class.html', upcoming_classes=upcoming_classes)

@app.route("/historic/")
def historic():
    #TODO: pull historic classes from database
    return render_template('historic.html')

@app.route("/instructors/")
def instructors():
    #TODO: pull upcoming classes from database
    return render_template('instructors.html')

# launch
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
