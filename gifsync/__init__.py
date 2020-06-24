import base64
import os
from flask import Flask, flash, redirect, request, render_template, send_from_directory, url_for
from .forms import GifCreationForm

# from werkzeug.utils import secure_filename

app = Flask(__name__)
env = os.environ.get('FLASK_ENV', 'development')
app.config['ENV'] = env
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'devkey')


@app.route('/')
def index():
    return redirect(url_for('home'))


@app.route("/home/")
def home():
    print(app.config['SECRET_KEY'])
    return render_template('home.html', title='Home')


@app.route("/collection/")
def collection():
    test_images = []
    for i in range(1, 14):
        test_images.append({
            'src': url_for('static', filename='img/image-placeholder.png'),
            'label': f'Image #{i}'
        })
    return render_template('collection.html', title='My Gifs', images=test_images)


@app.route('/create/', methods=['GET', 'POST'])
def create():
    form = GifCreationForm()
    if request.method == 'POST' and form.validate_on_submit():
        filename = form.gif_file.data.filename
        if '.' in filename and filename.rsplit('.', 1)[1].lower() == 'gif':
            return redirect(url_for('show'), code=307)
        else:
            flash('You must select a file (Only .gif files are allowed)', 'danger')
            render_template('create.html', title='New Gif', form=form)
    return render_template('create.html', title='New Gif', form=form)


@app.route('/show/', methods=['GET', 'POST'])
def show():
    # TODO: This is temporary. Will move to storing images in database.
    if request.method == 'POST' and request.files.get('gif_file'):
        b64_file = base64.b64encode(request.files.get("gif_file").stream.read()).decode('utf-8')
        image_src = f'data:image/gif;base64,{b64_file}'
    else:
        image_src = url_for('static', filename='img/image-placeholder.png')
    return render_template('show.html', title='Synced Gif', synced_image=image_src)


@app.route('/favicon.ico/')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'img/favicon.ico', mimetype='image/vnd.microsoft.icon')
