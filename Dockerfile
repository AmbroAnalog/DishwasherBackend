# FROM python:3.6.12-alpine
FROM python:3.9-alpine

RUN apk add build-base
RUN apk add curl

COPY requirements.txt /
RUN pip3 install -r /requirements.txt

COPY . /app
WORKDIR /app

RUN ["chmod", "+x", "./gunicorn.sh"]

ENTRYPOINT ["./gunicorn.sh"]

HEALTHCHECK --interval=10s --timeout=10s --start-period=55s \
   CMD curl -f --retry 10 --max-time 15 --retry-delay 10 --retry-max-time 60 "http://localhost:80/health" || exit 1   
