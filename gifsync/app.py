from flask import Flask, render_template, url_for

app = Flask(__name__)


@app.route("/")
@app.route("/home/")
@app.route("/about/")
def about():
    return render_template('about.html', title='Home')


@app.route("/collection/")
def collection():
    return render_template('collection.html', title='My Gifs')


@app.route('/create/')
def create():
    return render_template('create.html', title='New Gif')


@app.route('/show/')
def show():
    return render_template('show.html', title='Synced Gif')


if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True)
