import flask
import os
from scripts.build import build

app = flask.Flask(__name__, static_folder='static', static_url_path='')
app.secret_key = os.environ.get("SECRET_KEY")

@app.route("/", methods=['GET', 'POST'])
def index():
    if flask.request.method == 'POST':
        if 'password' in list(flask.request.form):
            if flask.request.form['password'] == os.environ.get("PASSWORD"):
                flask.session['authenticated'] = True
                return flask.render_template('output.html')
            else:
                flask.session['authenticated'] = False
                return flask.render_template('error.html')
            
    flask.session['authenticated'] = False      
    return flask.render_template('index.html')


@app.route("/buildepub", methods=['GET', 'POST'])
def buildepub():
    if not flask.session.get('authenticated'):
        yield('Not authenticated!' + "\n\n")
        return
    else:
        build()
        return flask.send_file('output.epub', as_attachment=True)




if __name__ == "__main__":
    app.run(host="0.0.0.0", port=os.environ.get("LOCAL_PORT", 5000), debug=os.environ.get("DEBUG", False), threaded=True)