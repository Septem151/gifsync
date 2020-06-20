"""
    Entry point for running a GifSync server.
"""
from gifsync import app


def develop_mode():
    """
    Runs the server in debug/develop mode. Should be used when developing to prevent the need of restarting the local
    server after changes made to HTML. Does **NOT** update CSS changes automatically, requiring a Hard Reload of web
    browser.

    :return: None
    """
    app.run(host='0.0.0.0', debug=True)


def production_mode():
    app.config['ENV'] = 'Production'
    app.run()


if __name__ == '__main__':
    production_mode()
