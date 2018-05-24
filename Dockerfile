# python:alpine is 3.6.{latest}
FROM python:3.6.5-alpine

RUN apk --update add libxml2-dev libxslt-dev libffi-dev gcc musl-dev libgcc openssl-dev curl
RUN apk add jpeg-dev zlib-dev freetype-dev lcms2-dev openjpeg-dev tiff-dev tk-dev tcl-dev

COPY requirements.txt  /src/requirements.txt
COPY schema.sql  /src/schema.sql
COPY static /src/static/
COPY templates /src/templates/
COPY trocr.py  /src/trocr.py
COPY websiteconfig.py.sample  /src/websiteconfig.py

WORKDIR /src

RUN pip install -Ur requirements.txt
RUN pip install gunicorn

EXPOSE 8000

ENTRYPOINT ["gunicorn", "-b", "0.0.0.0", "trocr:app"]
