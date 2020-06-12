import os
from flask import Flask, render_template, url_for, send_from_directory

app = Flask(__name__)


@app.route("/")
@app.route("/home/")
def home(title='Home'):
    return render_template('about.html', title=title)


@app.route("/about/")
def about():
    return home('About')


@app.route("/collection/")
def collection():
    return render_template('collection.html', title='My Gifs')


@app.route('/create/')
def create():
    return render_template('create.html', title='New Gif')


@app.route('/show/')
def show():
    return render_template('show.html', title='Synced Gif')


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')
