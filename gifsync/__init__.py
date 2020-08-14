from datetime import datetime, timedelta
from flask import abort, Flask, flash, jsonify, make_response, redirect, render_template, request, \
                  send_file, send_from_directory, session, url_for
from flask_login import current_user, login_required, login_user
from flask_talisman import Talisman
from gifsync import config
from gifsync.extensions import db, login_manager
from gifsync.models.forms import GifCreationForm
from gifsync.models.gifs import Gif, Image
from gifsync.models.songs import Song
from gifsync.models.users import AnonymousUser, SpotifyUser
from io import BytesIO
from requests_oauthlib import OAuth2Session
from urllib.parse import urlparse, urljoin
import os
import shutil


def create_app():
    flask_app = Flask(__name__)
    flask_app.config['ENV'] = config.flask_env
    flask_app.config['SECRET_KEY'] = config.flask_secret
    flask_app.config['SQLALCHEMY_DATABASE_URI'] = config.db_url
    flask_app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(flask_app)
    login_manager.anonymous_user = AnonymousUser
    login_manager.init_app(flask_app)
    return flask_app


def is_safe_url(target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc


def retrieve_gif(gif_id, user_id):
    if not gif_id:
        abort(400)
    gif = Gif.query.filter(Gif.id == gif_id).first()
    if not gif:
        abort(404)
    if gif.user_id != user_id:
        abort(401)
    return gif


app = create_app()
if not app.config['ENV'] == 'development':
    Talisman(app, content_security_policy=config.csp)
else:
    # Manually set OAUTHLIB_INSECURE_TRANSPORT so we don't have to include it in environment variables
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'


@app.errorhandler(400)
@app.errorhandler(401)
@app.errorhandler(404)
def error_page(error):
    return render_template('error.html', error=str(error).split(':')), error.code


@login_manager.user_loader
def load_user(user_id):
    return SpotifyUser.query.filter(SpotifyUser.id == str(user_id)).first()


@login_manager.unauthorized_handler
def unauthorized():
    if request.path == url_for('logout'):
        return redirect(url_for('home'))
    return redirect(url_for('login', next=request.url))


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
    gif = retrieve_gif(gif_id, current_user.get_id())
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


@app.route('/api/me/edit-gif', methods=['POST'])
@login_required
def api_edit_gif():
    gif_id = request.args.get('id')
    gif_name = request.args.get('name')
    gif_bpl = request.args.get('bpl')
    gif = retrieve_gif(gif_id, current_user.get_id())
    if gif_name and gif_name != gif.name:
        gif_name = gif_name.strip()
        if not 1 <= len(gif_name) <= 64:
            return jsonify({'status': 'error', 'reason': 'New name must be between 1-64 characters in length.'})
        for user_gif in current_user.gifs:
            if user_gif.name.strip() == gif_name:
                return jsonify({'status': 'error', 'reason': 'You already have a Gif called that! Try a unique name.'})
        gif.update_name(gif_name)
    if gif_bpl:
        try:
            gif_bpl = int(gif_bpl)
        except (TypeError, ValueError):
            return jsonify({'status': 'error', 'reason': 'Only whole numbers are allowed for Beats per loop.'})
        if not 1 <= gif_bpl <= 64:
            return jsonify({'status': 'error', 'reason': 'Beats per loop value must be between 1-64.'})
        gif.beats_per_loop = gif_bpl
    if gif_name or gif_bpl:
        db.session.commit()
    return jsonify({'status': 'OK', 'gif_id': gif.id, 'gif_name': gif.name, 'gif_bpl': gif.beats_per_loop})


@app.route('/api/me/image')
@login_required
def api_user_image():
    gif_id = request.args.get('gif_id')
    gif = retrieve_gif(gif_id, current_user.get_id())
    response = make_response(send_file(BytesIO(gif.image.image), mimetype='image/gif'))
    response.headers['Cache-control'] = 'max-age=2592000, private'
    return response


@app.route('/api/me/synced-gif')
@login_required
def api_synced_gif():
    gif_id = request.args.get('gif_id')
    song_id = request.args.get('song_id')
    gif = retrieve_gif(gif_id, current_user.get_id())
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
    if not session.get('oauth_state') or len(request.args) != 2 or 'error' in request.args \
            or ('code' not in request.args and 'state' not in request.args):
        flash('There was an error logging you in.', category='danger')
        return redirect(url_for('index'))
    spotify_oauth = OAuth2Session(config.client_id, redirect_uri=config.callback_uri, state=session['oauth_state'])
    token = spotify_oauth.fetch_token(config.token_url, client_secret=config.client_secret,
                                      authorization_response=request.url)
    access_token = token['access_token']
    expires_in = float(token['expires_in'])
    expiration_time = datetime.utcnow() + timedelta(seconds=expires_in)
    refresh_token = token['refresh_token']
    user = SpotifyUser(access_token, expiration_time, refresh_token)
    if not SpotifyUser.query.filter(SpotifyUser.id == user.get_id()).first():
        db.session.add(user)
        # Insert hat kid image into user's collection by default
        with open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               'static/img/hat-kid-smug-dance.gif'), 'rb') as image:
            hat_kid_image = Image(image.read())
        if not Image.query.filter(Image.id == hat_kid_image.id).first():
            db.session.add(hat_kid_image)
        hat_kid_gif = Gif(user.id, hat_kid_image.id, 'Hat Kid', 2)
        db.session.add(hat_kid_gif)
        db.session.commit()
    login_user(user)
    next_url = session.get('next')
    if not is_safe_url(next_url):
        abort(400)
    if next_url:
        session.pop('next')
    session.pop('oauth_state')
    return redirect(next_url or url_for('collection'))


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
        gif_name = form.gif_name.data.strip()
        user_gifs = current_user.gifs
        for user_gif in user_gifs:
            if user_gif.name.strip() == gif_name:
                flash('You already have a Gif called that! Try a unique name.', category='danger')
                return render_template('create.html', title='New Gif', form=form)
        filename = form.gif_file.data.filename
        if '.' in filename and filename.rsplit('.', 1)[1].lower() == 'gif':
            image_data = form.gif_file.data.stream.read()
            size = len(image_data)
            if size > 6 * 1024 * 1024:
                flash('File is too large! Maximum Gif size is 6MB. Try a smaller file.', category='danger')
                return render_template('create.html', title='New Gif', form=form)
            file = Image(image_data)
            if not Image.query.filter(Image.id == file.id).first():
                db.session.add(file)
                db.session.commit()
            user_gif = Gif(current_user.get_id(), file.id, gif_name, form.beats_per_loop.data)
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


@app.route('/keybase.txt')
def keybase():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'keybase.txt', mimetype='text/plain')


@app.route('/login')
def login():
    spotify_oauth = OAuth2Session(config.client_id, scope=config.scope, redirect_uri=config.callback_uri)
    authorization_url, state = spotify_oauth.authorization_url(config.authorization_base_url, show_dialog='true')
    session['oauth_state'] = state
    next_url = request.args.get('next')
    if next_url:
        session['next'] = next_url
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


@app.route('/privacy')
def privacy_policy():
    return render_template('privacy.html')


@app.route('/show', methods=['GET'])
@login_required
def show():
    gif_id = request.args.get('gif_id')
    gif = retrieve_gif(gif_id, current_user.get_id())
    if not gif.image.is_saved_as_frames:
        flash('Gifs may take a few seconds to load when first created! '
              'If still not loaded after 30 seconds, try refreshing the page.', category='warning')
    return render_template('show.html', title=gif.name, gif=gif)
