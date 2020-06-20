import os
from flask import Flask, redirect, request, render_template, send_from_directory, url_for

app = Flask(__name__)


@app.before_request
def remove_trailing_slashes():
    request_path = request.path
    if request_path != '/' and request_path.endswith('/'):
        return redirect(request_path[:-1])


@app.route('/')
def index():
    return redirect(url_for('home'))


@app.route("/home")
def home():
    return render_template('home.html', title='Home')


@app.route("/collection")
def collection():
    return render_template('collection.html', title='My Gifs')


@app.route('/create')
def create():
    return render_template('create.html', title='New Gif')


@app.route('/show')
def show():
    return render_template('show.html', title='Synced Gif')


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'img/favicon.ico', mimetype='image/vnd.microsoft.icon')
