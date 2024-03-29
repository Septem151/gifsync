import os
from datetime import datetime, timedelta
from http import HTTPStatus
from io import BytesIO
from urllib.parse import urljoin, urlparse

from flask import (
    Flask,
    abort,
    flash,
    jsonify,
    make_response,
    redirect,
    render_template,
    request,
    send_file,
    send_from_directory,
    session,
    url_for,
)
from flask_login import current_user, login_required, login_user, logout_user
from flask_talisman import Talisman
from requests_oauthlib import OAuth2Session

from gifsync import config
from gifsync.extensions import db, login_manager
from gifsync.models.forms import GifCreationForm, PreferencesForm
from gifsync.models.gifs import Gif, Image
from gifsync.models.songs import Song
from gifsync.models.users import AnonymousUser, SpotifyUser


def create_app():
    flask_app = Flask(__name__)
    flask_app.config["DEBUG"] = config.flask_debug
    flask_app.config["SECRET_KEY"] = config.flask_secret
    flask_app.config["SQLALCHEMY_DATABASE_URI"] = config.db_url
    flask_app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    flask_app.config["REMEMBER_COOKIE_DURATION"] = config.REMEMBER_COOKIE_DURATION
    db.init_app(flask_app)
    login_manager.anonymous_user = AnonymousUser
    login_manager.init_app(flask_app)
    return flask_app


def is_safe_url(target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ("http", "https") and ref_url.netloc == test_url.netloc


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
if app.config["DEBUG"] is False:
    Talisman(app, content_security_policy=config.csp)
else:
    # Manually set OAUTHLIB_INSECURE_TRANSPORT so we don't have to include it
    # in environment variables
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"


@app.errorhandler(400)
@app.errorhandler(401)
@app.errorhandler(403)
@app.errorhandler(404)
def error_page(error):
    return (render_template("error.html", error=str(error).split(":")), error.code)


@login_manager.user_loader
def load_user(user_id):
    return SpotifyUser.query.filter(SpotifyUser.id == str(user_id)).first()


@login_manager.unauthorized_handler
def unauthorized():
    if request.path == url_for("logout"):
        return redirect(url_for("home"))
    return redirect(url_for("login", next=request.url))


@app.route("/")
def index():
    return redirect(url_for("home"))


@app.route("/api/me/current-song")
def api_curr_song():
    if not current_user.is_authenticated:
        abort(HTTPStatus.FORBIDDEN)
    current_user.update_curr_song()
    return jsonify(current_user.curr_song)


@app.route("/api/me/delete-gif")
def api_delete_gif():
    if not current_user.is_authenticated:
        abort(HTTPStatus.FORBIDDEN)
    gif_id = request.args.get("id")
    gif = retrieve_gif(gif_id, current_user.get_id())
    db.session.delete(gif)
    db.session.commit()
    # Delete all images not being referenced by a gif to clean up the database
    # & local files
    db.session.execute(
        "DELETE FROM image imid WHERE NOT EXISTS (SELECT FROM gif"  # type: ignore
        " WHERE image_id = imid.id)"
    )
    db.session.commit()
    return redirect(url_for("collection"))


@app.route("/api/me/edit-gif", methods=["POST"])
def api_edit_gif():  # pylint: disable=too-many-branches
    if not current_user.is_authenticated:
        abort(HTTPStatus.FORBIDDEN)
    gif_id = request.args.get("id")
    gif_name = request.args.get("name")
    gif_bpl = request.args.get("bpl")
    gif_tempo = request.args.get("tempo")
    gif = retrieve_gif(gif_id, current_user.get_id())
    if gif_name and gif_name != gif.name:
        gif_name = gif_name.strip()
        if not 1 <= len(gif_name) <= 64:
            return jsonify(
                {
                    "status": "error",
                    "reason": (
                        "New name must be between " "1-64 characters in length."
                    ),
                }
            )
        for user_gif in current_user.gifs:
            if user_gif.name.strip() == gif_name:
                return jsonify(
                    {
                        "status": "error",
                        "reason": (
                            "You already have a Gif " "called that! Try a unique name."
                        ),
                    }
                )
        gif.update_name(gif_name)
    if gif_bpl:
        try:
            new_gif_bpl = int(gif_bpl)
        except (TypeError, ValueError):
            return jsonify(
                {
                    "status": "error",
                    "reason": ("Only whole numbers are allowed " "for Beats per loop."),
                }
            )
        if not 1 <= new_gif_bpl <= 64:
            return jsonify(
                {
                    "status": "error",
                    "reason": ("Beats per loop value must be " "between 1-64."),
                }
            )
        gif.beats_per_loop = new_gif_bpl
    ret_data = {
        "status": "OK",
        "gif_id": gif.id,
        "gif_name": gif.name,
        "gif_bpl": gif.beats_per_loop,
    }
    if gif_tempo:
        try:
            new_gif_tempo = float(gif_tempo)
            if new_gif_tempo < 0:
                raise ValueError()
        except (TypeError, ValueError):
            return jsonify(
                {
                    "status": "error",
                    "reason": "Tempo wasn't a number, or was less than 0",
                }
            )
        if new_gif_tempo == 0:
            gif.custom_tempo = None
        else:
            gif.custom_tempo = new_gif_tempo
            ret_data["gif_tempo"] = new_gif_tempo
    if gif_name or gif_bpl or gif_tempo:
        db.session.commit()
    return jsonify(ret_data)


@app.route("/api/me/image")
def api_user_image():
    if not current_user.is_authenticated:
        abort(HTTPStatus.FORBIDDEN)
    gif_id = request.args.get("gif_id")
    gif = retrieve_gif(gif_id, current_user.get_id())
    response = make_response(send_file(BytesIO(gif.image.image), mimetype="image/gif"))
    response.headers["Cache-control"] = "max-age=2592000, private"
    return response


@app.route("/api/me/image/thumbnail")
def api_user_image_thumbnail():
    if not current_user.is_authenticated:
        abort(HTTPStatus.FORBIDDEN)
    gif_id = request.args.get("gif_id")
    gif = retrieve_gif(gif_id, current_user.get_id())
    if not gif.image.thumbnail:
        gif.image.thumbnail = gif.image.generate_thumbnail()
        db.session.commit()
    response = make_response(
        send_file(BytesIO(gif.image.thumbnail), mimetype="image/gif")
    )
    response.headers["Cache-control"] = "max-age=2592000, private"
    return response


@app.route("/api/me/synced-gif")
def api_synced_gif():
    if not current_user.is_authenticated:
        abort(HTTPStatus.FORBIDDEN)
    gif_id = request.args.get("gif_id")
    song_id = request.args.get("song_id")
    gif = retrieve_gif(gif_id, current_user.get_id())
    if not song_id:
        song_id = "placeholdersong"
    tempo = gif.custom_tempo or current_user.clamp_tempo(
        Song.get_song_tempo(song_id, current_user.access_token)
    )
    if not tempo:
        abort(404)
    synced_image = gif.get_synced_gif(tempo)
    response = make_response(send_file(BytesIO(synced_image), mimetype="image/gif"))
    response.headers["Cache-control"] = "no-store"
    return response


@app.route("/api/me/cleanup")
def api_cleanup():
    if not current_user.is_authenticated:
        abort(HTTPStatus.FORBIDDEN)
    # Delete the current user, which deletes all of their gifs
    db.session.delete(current_user)
    db.session.commit()
    # Delete all images not being referenced by a gif to clean up the database
    # & local files
    db.session.execute(
        "DELETE FROM image imid WHERE NOT EXISTS (SELECT FROM gif"  # type: ignore
        " WHERE image_id = imid.id)"
    )
    db.session.commit()
    return redirect(url_for("logout"))


@app.route("/callback", methods=["GET"])
def callback():
    if (
        len(request.args) != 2
        or "error" in request.args
        or ("code" not in request.args and "state" not in request.args)
    ):
        flash("There was an error logging you in.", category="danger")
        return redirect(url_for("index"))
    login_session = session.get("login", {})
    state = request.args["state"]
    if state not in login_session:
        flash(
            "There was an error logging you in. [CSRF State Token invalid]",
            category="danger",
        )
        return redirect(url_for("index"))
    spotify_oauth = OAuth2Session(
        config.client_id, redirect_uri=config.callback_uri, state=state
    )
    token = spotify_oauth.fetch_token(
        config.TOKEN_URL,
        client_secret=config.client_secret,
        authorization_response=request.url,
    )
    access_token = token["access_token"]
    expires_in = float(token["expires_in"])
    expiration_time = datetime.utcnow() + timedelta(seconds=expires_in)
    refresh_token = token["refresh_token"]
    user = SpotifyUser(access_token, expiration_time, refresh_token)
    if not SpotifyUser.query.filter(SpotifyUser.id == user.get_id()).first():
        db.session.add(user)
        # Insert hat kid image into user's collection by default
        with open(
            os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "static/img/hat-kid-smug-dance.gif",
            ),
            "rb",
        ) as image:
            hat_kid_image = Image(image.read())
        if not Image.query.filter(Image.id == hat_kid_image.id).first():
            db.session.add(hat_kid_image)
        hat_kid_gif = Gif(user.id, hat_kid_image.id, "Hat Kid", 2)
        db.session.add(hat_kid_gif)
        db.session.commit()
    login_user(user, remember=True)
    state_obj = login_session.pop(state)
    next_url = state_obj.get("next")
    session["login"] = login_session
    if next_url and not is_safe_url(next_url):
        abort(400)
    return redirect(next_url or url_for("collection"))


@app.route("/collection")
@login_required
def collection():
    user_gifs = current_user.gifs
    images = []
    for gif in user_gifs:
        images.append(
            {
                "src": url_for("api_user_image_thumbnail", gif_id=gif.id),
                "label": gif.name,
                "href": url_for("show", gif_id=gif.id),
            }
        )
    return render_template("collection.html", title="My Gifs", images=images)


@app.route("/preferences", methods=["GET", "POST"])
@login_required
def preferences():
    form = PreferencesForm()
    user_prefs: dict | None = current_user.preferences
    new_prefs: dict = {}
    if request.method == "POST" and form.validate_on_submit():
        min_tempo = form.min_tempo.data
        max_tempo = form.max_tempo.data
        if min_tempo and max_tempo:
            if min_tempo >= max_tempo:
                flash(
                    "Minimum Tempo cannot be less than Maximum Tempo!",
                    category="danger",
                )
                return render_template(
                    "preferences.html",
                    title="Settings",
                    form=form,
                    user_prefs=user_prefs,
                )
            if max_tempo < min_tempo:
                flash(
                    "Maximum Tempo cannot be less than Minimum Tempo!",
                    category="danger",
                )
                return render_template(
                    "preferences.html",
                    title="Settings",
                    form=form,
                    user_prefs=user_prefs,
                )
        if min_tempo:
            new_prefs["min_tempo"] = min_tempo
        if max_tempo:
            new_prefs["max_tempo"] = max_tempo
        if len(new_prefs) != 0:
            current_user.preferences = new_prefs
        else:
            current_user.preferences = None
        db.session.commit()
        return render_template(
            "preferences.html", title="Settings", form=form, user_prefs=new_prefs
        )
    return render_template(
        "preferences.html", title="Settings", form=form, user_prefs=user_prefs
    )


@app.route("/create", methods=["GET", "POST"])
@login_required
def create():
    form = GifCreationForm()
    if request.method == "POST" and form.validate_on_submit():
        gif_name = form.gif_name.data.strip()
        user_gifs = current_user.gifs
        for user_gif in user_gifs:
            if user_gif.name.strip() == gif_name:
                flash(
                    "You already have a Gif called that! Try a unique name.",
                    category="danger",
                )
                return render_template("create.html", title="New Gif", form=form)
        filename = form.gif_file.data.filename
        if "." in filename and filename.rsplit(".", 1)[1].lower() == "gif":
            image_data = form.gif_file.data.stream.read()
            size = len(image_data)
            if size > 64 * 1024 * 1024:
                flash(
                    (
                        "File is too large! Maximum Gif size is 64MB. "
                        "Try a smaller file."
                    ),
                    category="danger",
                )
                return render_template("create.html", title="New Gif", form=form)
            file = Image(image_data)
            if not Image.query.filter(Image.id == file.id).first():
                db.session.add(file)
                db.session.commit()
            user_gif = Gif(
                current_user.get_id(), file.id, gif_name, form.beats_per_loop.data
            )
            db.session.add(user_gif)
            db.session.commit()
            return redirect(url_for("show", gif_id=user_gif.id))
        flash("You must select a file (Only .gif files are allowed)", "danger")
    return render_template("create.html", title="New Gif", form=form)


@app.route("/favicon.ico")
def favicon():
    return send_from_directory(
        os.path.join(app.root_path, "static"),
        "img/favicon.ico",
        mimetype="image/vnd.microsoft.icon",
    )


@app.route("/home")
def home():
    return render_template("home.html", title="Home")


@app.route("/keybase.txt")
def keybase():
    return send_from_directory(
        os.path.join(app.root_path, "static"), "keybase.txt", mimetype="text/plain"
    )


@app.route("/login")
def login():
    spotify_oauth = OAuth2Session(
        config.client_id, scope=config.scope, redirect_uri=config.callback_uri
    )
    authorization_url, state = spotify_oauth.authorization_url(
        config.AUTHORIZATION_BASE_URL, show_dialog="true"
    )
    next_url = request.args.get("next")
    login_session = session.get("login", {})
    login_session.update(
        {state: {"next": next_url}},
    )
    session["login"] = login_session
    session.modified = True
    return redirect(authorization_url)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("home"))


@app.route("/privacy")
def privacy_policy():
    return render_template("privacy.html")


@app.route("/show", methods=["GET"])
@login_required
def show():
    gif_id = request.args.get("gif_id")
    gif = retrieve_gif(gif_id, current_user.get_id())
    return render_template("show.html", title=gif.name, gif=gif)
