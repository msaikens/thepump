import os
from flask import Flask, render_template, send_from_directory

# initialization
app = Flask(__name__)
app.config.update(
    DEBUG = True,
)

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

@app.route("/current/")
def current():
    #TODO: pull class details for selected class
    return render_template('current.html')

@app.route("/upcoming/")
def upcoming():
    #TODO: pull upcoming classes from database
    return render_template('upcoming.html')

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
