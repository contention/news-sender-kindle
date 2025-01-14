import flask
import os

app = flask.Flask(__name__, static_folder='static', static_url_path='')

@app.route("/", methods=['GET', 'POST'])
def index():
    if flask.request.method == 'POST':
        if 'password' in list(flask.request.form):
            if flask.request.form['password'] == os.environ.get("PASSWORD"):
                return flask.render_template('build.html')
            else:
                return flask.render_template('index.html')
    return flask.render_template('index.html')

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=os.environ.get("LOCAL_PORT", 5000), debug=os.environ.get("DEBUG", False), threaded=True)