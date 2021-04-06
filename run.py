from gifsync import create_app
from config import config

app = create_app()

@app.errorhandler(400)
@app.errorhandler(401)
@app.errorhandler(404)
def error_page(error):
    return render_template(
        'error.html',
        error=str(error).split(':')
    ), error.code

if __name__ == '__main__':
    app.run(
        host='0.0.0.0', 
        port=config.PORT,
        debug=config.DEBUG
    )