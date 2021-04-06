import os

from flask import Flask
from flask_talisman import Talisman
from urllib.parse import urlparse, urljoin

from .extensions import db, login_manager
from .models.users import AnonymousUser

def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')

    from .core.routes import blueprint as core_bp
    from .api.routes import blueprint as api_bp
    from .user.routes import blueprint as user_bp

    app.register_blueprint(core_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(user_bp)

    register_extensions(app)

    return app


def register_extensions(app):
    db.init_app(app)

    login_manager.anonymous_user = AnonymousUser
    login_manager.login_view = 'user.login'
    login_manager.init_app(app)

    if not app.config['ENV'] == 'development':
        Talisman(app, content_security_policy=app.config['CSP'])
    else:
        os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

    @login_manager.user_loader
    def load_user(user_id):
        return SpotifyUser.query.get(int(user_id))

    @login_manager.unauthorized_handler
    def unauthorized():
        if request.path == url_for('user.logout'):
            return redirect(url_for('core.home'))

        return redirect(url_for('user.login', next=request.url))


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