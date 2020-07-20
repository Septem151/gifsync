from . import config
from .extensions import db, login_manager
from .models.forms import GifCreationForm
from .models.gifs import Gif, Image
from .models.songs import Song
from .models.users import AnonymousUser, SpotifyUser
from datetime import datetime, timedelta
from flask import abort, flash, Flask, jsonify, make_response, redirect, render_template, request, \
    send_file, send_from_directory, session, url_for
from flask_login import current_user, login_required, login_user
from flask_talisman import Talisman
import os
from requests_oauthlib import OAuth2Session
import shutil


def create_app():
    flask_app = Flask(__name__)
    flask_app.config['ENV'] = config.flask_env
    flask_app.config['SECRET_KEY'] = config.flask_secret
    flask_app.config['SQLALCHEMY_DATABASE_URI'] = config.db_url
    db.init_app(flask_app)
    login_manager.anonymous_user = AnonymousUser
    login_manager.init_app(flask_app)
    return flask_app


app = create_app()
if not app.config['ENV'] == 'development':
    Talisman(app, content_security_policy=config.csp)
else:
    # Manually set OAUTHLIB_INSECURE_TRANSPORT so we don't have to include it in environment variables
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'


@login_manager.user_loader
def load_user(user_id):
    return SpotifyUser.query.filter(SpotifyUser.id == str(user_id)).first()


@app.route('/')
def index():
    return redirect(url_for('home'))


@app.route('/api/me/current-song')
@login_required
def api_curr_song():
    current_user.update_curr_song()
    return jsonify(current_user.curr_song)


@app.route('/api/me/delete-gif')
@login_required
def api_delete_gif():
    gif_id = request.args.get('id')
    if not gif_id:
        abort(400)
    gif = Gif.query.filter(Gif.id == gif_id).first()
    if not gif:
        abort(404)
    if gif.user_id != current_user.get_id():
        abort(401)
    db.session.delete(gif)
    db.session.commit()
    # Delete all images not being referenced by a gif to clean up the database & local files
    image_query_result = db.session.execute(
        'SELECT id FROM image imid WHERE NOT EXISTS (SELECT FROM gif WHERE image_id = imid.id)')
    for result in image_query_result:
        image_id = result['id']
        image_frames_folder = os.path.join(config.gif_frames_path, str(image_id))
        if os.path.exists(image_frames_folder):
            shutil.rmtree(image_frames_folder)
    db.session.execute('DELETE FROM image imid WHERE NOT EXISTS (SELECT FROM gif WHERE image_id = imid.id)')
    db.session.commit()
    return redirect(url_for('collection'))


@app.route('/api/me/image')
@login_required
def api_user_image():
    gif_id = request.args.get('gif_id')
    if not gif_id:
        abort(400)
    gif = Gif.query.filter(Gif.id == gif_id).first()
    if not gif:
        abort(404)
    if gif.user_id != current_user.get_id():
        abort(401)
    response = make_response(gif.image.image)
    response.headers['Cache-control'] = 'no-store'
    return response


@app.route('/api/me/synced-gif')
@login_required
def api_synced_gif():
    gif_id = request.args.get('gif_id')
    song_id = request.args.get('song_id')
    if not gif_id:
        abort(400)
    gif = Gif.query.filter(Gif.id == gif_id).first()
    if not gif:
        abort(404)
    if gif.user_id != current_user.get_id():
        abort(401)
    if not song_id:
        song_id = 'placeholdersong'
    tempo = Song.get_song_tempo(song_id, current_user.access_token)
    if not tempo:
        abort(404)
    synced_image = gif.get_synced_gif(tempo)
    synced_image.seek(0, 0)
    response = make_response(send_file(synced_image, mimetype='image/gif'))
    response.headers['Cache-control'] = 'no-store'
    return response


@app.route('/callback', methods=['GET'])
def callback():
    if len(request.args) != 2 or 'error' in request.args \
            or ('code' not in request.args and 'state' not in request.args):
        return redirect(url_for('index'))
    spotify_oauth = OAuth2Session(config.client_id, redirect_uri=config.callback_uri, state=session['oauth_state'])
    token = spotify_oauth.fetch_token(config.token_url, client_secret=config.client_secret,
                                      authorization_response=request.url)
    access_token = token['access_token']
    expires_in = float(token['expires_in'])
    expiration_time = datetime.utcnow() + timedelta(seconds=expires_in)
    refresh_token = token['refresh_token']
    user = SpotifyUser(access_token, expiration_time, refresh_token)
    if not load_user(user.get_id()):
        db.session.add(user)
        db.session.commit()
    login_user(user)
    return redirect(url_for('collection'))


@app.route("/collection")
@login_required
def collection():
    user_gifs = current_user.gifs
    images = []
    for gif in user_gifs:
        images.append({
            'src': url_for('api_user_image', gif_id=gif.id),
            'label': gif.name,
            'href': url_for('show', gif_id=gif.id)
        })
    return render_template('collection.html', title='My Gifs', images=images)


@app.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    form = GifCreationForm()
    if request.method == 'POST' and form.validate_on_submit():
        user_gifs = current_user.gifs
        for user_gif in user_gifs:
            if user_gif.name == form.gif_name.data:
                flash('You already have a Gif called that! Try a unique name.', 'danger')
                return render_template('create.html', title='New Gif', form=form)
        filename = form.gif_file.data.filename
        if '.' in filename and filename.rsplit('.', 1)[1].lower() == 'gif':
            file = Image(form.gif_file.data.stream.read())
            if not Image.query.filter(Image.id == file.id).first():
                db.session.add(file)
                db.session.commit()
            user_gif = Gif(current_user.get_id(), file.id, form.gif_name.data, form.beats_per_loop.data)
            db.session.add(user_gif)
            db.session.commit()
            return redirect(url_for('show', gif_id=user_gif.id))
        else:
            flash('You must select a file (Only .gif files are allowed)', 'danger')
    return render_template('create.html', title='New Gif', form=form)


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'img/favicon.ico', mimetype='image/vnd.microsoft.icon')


@app.route("/home")
def home():
    return render_template('home.html', title='Home')


@app.route('/login')
def login():
    spotify_oauth = OAuth2Session(config.client_id, scope=config.scope, redirect_uri=config.callback_uri)
    authorization_url, state = spotify_oauth.authorization_url(config.authorization_base_url, show_dialog='true')
    session['oauth_state'] = state
    return redirect(authorization_url)


@app.route('/logout')
@login_required
def logout():
    # Delete the current user, which deletes all of their gifs
    db.session.delete(current_user)
    db.session.commit()
    # Delete all images not being referenced by a gif to clean up the database & local files
    image_query_result = db.session.execute(
        'SELECT id FROM image imid WHERE NOT EXISTS (SELECT FROM gif WHERE image_id = imid.id)')
    for result in image_query_result:
        image_id = result['id']
        image_frames_folder = os.path.join(config.gif_frames_path, str(image_id))
        if os.path.exists(image_frames_folder):
            shutil.rmtree(image_frames_folder)
    db.session.execute('DELETE FROM image imid WHERE NOT EXISTS (SELECT FROM gif WHERE image_id = imid.id)')
    db.session.commit()
    return redirect(url_for('home'))


@app.route('/show', methods=['GET'])
@login_required
def show():
    gif_id = request.args.get('gif_id')
    if not gif_id:
        abort(400)
    gif = Gif.query.filter(Gif.id == gif_id).first()
    if gif:
        if gif.user_id == current_user.get_id():
            return render_template('show.html', title=gif.name, gif_id=gif_id)
        else:
            abort(401)
    else:
        abort(404)
