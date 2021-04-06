from flask import Blueprint, render_template

blueprint = Blueprint('core', __name__, template_folder='templates')

@blueprint.route('/')
@blueprint.route('/home')
@blueprint.route('/about')
def index():
    return render_template('home.html', title='Home')

@blueprint.route('/privacy')
def privacy_policy():
    return render_template('privacy.html')

@blueprint.route('/favicon.ico')
def favicon():
    return send_from_directory(
        os.path.join(app.root_path, 'static'),
        'img/favicon.ico',
        mimetype='image/vnd.microsoft.icon'
    )

@blueprint.route('/keybase.txt')
def keybase():
    return send_from_directory(
        os.path.join(app.root_path, 'static'),
        'keybase.txt',
        mimetype='text/plain'
    )