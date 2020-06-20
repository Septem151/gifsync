"""
    Entry point for running a GifSync server.
"""
from gifsync import app
import os


def set_environment():
    """
    Sets which environment we should be running in: Production or Development

    :return: None
    """
    port = int(os.environ.get('PORT', '5000'))
    # Change this function call to either develop_mode(port) or production_mode(port)
    production_mode(port)


def develop_mode(port):
    """
    Runs the server in debug/develop mode. Should be used when developing to prevent the need of restarting the local
    server after changes made to HTML. Does **NOT** update CSS changes automatically, requiring a Hard Reload of web
    browser.

    :return: None
    """
    app.run(host='0.0.0.0', debug=True)


def production_mode(port):
    app.config['ENV'] = 'Production'
    app.run(host='0.0.0.0', port=port)


if __name__ == '__main__':
    set_environment()
