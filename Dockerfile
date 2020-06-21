FROM python:3.8-slim-buster
MAINTAINER Carson Mullins "carsonmullins@yahoo.com"
COPY . /app
WORKDIR /app
RUN pip3 install -r requirements.txt
CMD exec gunicorn -b 0.0.0.0:${PORT:-5000} --log-file=- --workers=2 --threads=4 --worker-class=gthread gifsync:app
