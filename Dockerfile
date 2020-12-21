FROM tiangolo/uvicorn-gunicorn-fastapi:python3.8

RUN mkdir -p /data/www/docs
RUN mkdir -p /data/www/help

COPY docker/index_redirect.html /data/www/docs/index.html
COPY docker/prestart.sh /app/prestart.sh

ENV APP_MODULE=docserver.core:app

COPY requirements.txt /app/requirements.txt

RUN pip install -r /app/requirements.txt
RUN pip install py_mini_racer psycopg2
ENV DOCSERVER_HELP_DIR=/data/www/help

CMD ["/start.sh"]

COPY docker-html-help /data/www/help
COPY docker-build /dist
RUN pip install /dist/$(ls -t /dist | head -n1) # pip install the latest created file in dist folder. this should be the wheel file.
