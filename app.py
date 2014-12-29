import os
from flask import Flask, request, render_template, send_from_directory

# initialization
app = Flask(__name__)


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
        return render_template('editclass.html')

    return render_template('showclass.html')

@app.route("/class/<int:class_id>/", methods=['POST'])
def update_class(class_id):
    #TODO: update class details, then show class

    edit = request.args.get('edit', 'false')

    if edit == 'true':
        #todo: send class data
        return render_template('editclass.html')

    return render_template('showclass.html')

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
