FROM tiangolo/uvicorn-gunicorn-fastapi:python3.7

RUN mkdir -p /data/www/docs

COPY docker/index_redirect.html /data/www/docs/index.html
COPY docker/prestart.sh /app/prestart.sh

ENV APP_MODULE=docserver.core:app

COPY requirements.txt /app/requirements.txt

RUN pip install -r /app/requirements.txt
RUN pip install py_mini_racer psycopg2

CMD ["/start.sh"]

COPY docker-build /dist
RUN pip install /dist/$(ls -t /dist | head -n1) # pip install the latest created file in dist folder. this should be the wheel file.
