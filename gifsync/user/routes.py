from flask import Blueprint, redirect, url_for, render_template
from flask_login import login_required

from gifsync.models.users import AnonymousUser, SpotifyUser

blueprint = Blueprint('user', __name__)

@blueprint.route('/login')
def login():
    spotify_oauth = OAuth2Session(
        config.client_id, scope=config.scope, redirect_uri=config.callback_uri)
    authorization_url, state = spotify_oauth.authorization_url(
        config.authorization_base_url, show_dialog='true')
    session['oauth_state'] = state
    next_url = request.args.get('next')
    if next_url:
        session['next'] = next_url
    return redirect(authorization_url)

@blueprint.route('/logout')
@login_required
def logout():
    # Delete the current user, which deletes all of their gifs
    db.session.delete(current_user)
    db.session.commit()
    # Delete all images not being referenced by a gif to clean up the database
    # & local files

    image_query_result = db.session.execute(
        'SELECT id FROM image imid WHERE NOT EXISTS (SELECT FROM gif'
        ' WHERE image_id = imid.id)'
    )
    for result in image_query_result:
        image_id = result['id']
        image_frames_folder = os.path.join(
            config.gif_frames_path, str(image_id))
        if os.path.exists(image_frames_folder):
            shutil.rmtree(image_frames_folder)
    db.session.execute(
        'DELETE FROM image imid WHERE NOT EXISTS (SELECT FROM gif'
        ' WHERE image_id = imid.id)'
    )
    db.session.commit()
    return redirect(url_for('home'))

@blueprint.route('/show', methods=['GET'])
@login_required
def show():
    gif_id = request.args.get('gif_id')
    gif = retrieve_gif(gif_id, current_user.get_id())

    if not gif.image.is_saved_as_frames:
        flash(
            'Gifs may take a few seconds to load when first created! '
            'If still not loaded after 30 seconds, try refreshing the page.',
            category='warning'
        )
    return render_template('show.html', title=gif.name, gif=gif)