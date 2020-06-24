"""
    Entry point for running a GifSync server without gunicorn.
    When running from Docker, the web.env file is used to manage the Port instead, and this file is not ran.
    Making changes when running via Docker does not require "development" or "debug" mode on changes.
    However, changes made will require a few seconds (10s or so) to be picked up.
"""
from gifsync import app
import os


if __name__ == '__main__':
    # YOU SHOULDN'T HAVE TO MODIFY THE PORT OR ENV! The Production server provided by flask is pointless.
    # Change the default port/environment by modifying the second parameter in "on.environ.get", OR by setting
    # environment variables for PORT and/or FLASK_ENV.
    # "development" env should be used when developing to prevent the need of restarting the
    # local server after changes made to HTML. Does NOT update CSS changes automatically, requiring a Hard Reload of
    # your web browser.
    # Valid env values: development, production
    port = int(os.environ.get('PORT', '5000'))
    if app.config['ENV'] == 'development':
        app.run(host='0.0.0.0', port=port, debug=True)
    else:
        app.run(host='0.0.0.0', port=port)
