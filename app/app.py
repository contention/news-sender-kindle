import flask
import os
import threading
from scripts.build import build
from flask_cors import CORS
from time import sleep

app = flask.Flask(__name__, static_folder='static', static_url_path='')
app.secret_key = os.environ.get("SECRET_KEY")
CORS(app)

@app.route("/", methods=['GET', 'POST'])
def index():
    if flask.request.method == 'POST':
        if 'password' in list(flask.request.form):
            if flask.request.form['password'] == os.environ.get("PASSWORD"):
                flask.session['authenticated'] = True
                threading.Thread(target=build).start()
                return flask.render_template('building.html')
            else:
                flask.session['authenticated'] = False
                return flask.render_template('error.html')
            
    flask.session['authenticated'] = False      
    return flask.render_template('index.html')



@app.route("/status", methods=['GET', 'POST'])
def checkstatus():
    if os.path.isfile("/output/status.txt"):
        f = open("/output/status.txt", "r")
        statustext = f.read()
        f.close()
        return app.response_class(statustext, mimetype="text/plain")
        
    else:
        return app.response_class("No status", mimetype="text/plain")
    


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=os.environ.get("LOCAL_PORT", 5000), debug=os.environ.get("DEBUG", False), threaded=True)