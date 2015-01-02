import os
from flask import Flask, request, render_template, send_from_directory
import json

# initialization
app = Flask(__name__)
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

@app.route("/class/<int:class_id>/", methods=['GET'])
def show_class(class_id):
    #TODO: pull class details for selected class
    edit = request.args.get('edit', 'false')

    if edit == 'true':
        #todo: send class data

        #fake data for now
        class_data={}

        class_data['students'] = {'student_0':{'name':"John Doe",'street_address':"123 Fake Street",'city_state':"Cofton, MD 21114"},'student_1':{'name':"Jane Doe",'street_address':"123 Fake Street",'city_state':"Cofton, MD 21114"},'student_2':{'name':"Jose Doe",'street_address':"123 Fake Street",'city_state':"Cofton, MD 21114"}}
        class_data['options'] = {'Child':'true',"Infants":'true','Written':'false'}
        class_data['class_date'] = "12/31/2014"
        class_data['class_id'] = 123
        class_data['curr_instructor'] = 12345
        class_data['curr_course_type'] = 1
        return render_edit_class(class_data, '')

    return render_template('showclass.html', class_data = "nop")

@app.route("/class/<int:class_id>/", methods=['POST'])
def update_class(class_id):
    #TODO: update class details, then show class

    edit = request.args.get('edit', 'false')

    #map request data into our data object
    class_data={}

    try:
        class_data['curr_instructor']=request.form['curr_instructor']
        class_data['class_date']=request.form['class_date']
        class_data['class_id']=class_id
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

    if edit == 'true':
        if os.environ['DEBUG'] == 'true':
            request_data = request.form
        else:
            request_data = ''

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
    edit = request.args.get('edit', 'false')

    if edit == 'true':
        #todo: create empty class, send class data
        return render_template('editclass.html')


    return render_template('class.html')

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
