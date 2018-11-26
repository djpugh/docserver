FROM tiangolo/uwsgi-nginx-flask:python3.7

RUN mkdir -p /data/www/docs

COPY docker/nginx/index_redirect.html /data/www/docs/index.html

ENV NGINX_MAX_UPLOAD 0


RUN rm /app/main.py

# Setup entrypoint
COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

COPY docker/flask/docserver.ini /app/uwsgi.ini
COPY docker/nginx/conf/ /etc/nginx/conf.d

COPY requirements.txt /app/requirements.txt

RUN pip install -r /app/requirements.txt

ENTRYPOINT ["/entrypoint.sh"]

CMD ["/start.sh"]

COPY docker-build /dist
RUN pip install /dist/$(ls -t /dist | head -n1) # pip install the latest created file in dist folder. this should be the wheel file.

RUN python -m docserver.models