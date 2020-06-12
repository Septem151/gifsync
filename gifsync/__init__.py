import os
from flask import Flask, redirect, render_template, send_from_directory, url_for

app = Flask(__name__)


@app.route('/')
def root():
    return redirect(url_for('home'))


@app.route("/home/")
def home():
    return render_template('home.html', title='Home')


@app.route("/about/")
def about():
    return redirect(url_for('home'))


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
