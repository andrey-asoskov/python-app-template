FROM python:3.9.14-alpine3.16

LABEL version="0.1.0" \
  description="The App"

HEALTHCHECK --interval=5s --timeout=3s --retries=3 --start-period=5s \
  CMD curl -f http://localhost:3000/health || exit 1

# hadolint ignore=DL3018
RUN apk add --no-cache curl

RUN adduser -u 1000 -s /bin/bash -D appuser && mkdir -p /usr/src/app
WORKDIR /usr/src/app

COPY ./app /usr/src/app
RUN pip3 install --no-cache-dir -r requirements.txt

USER appuser
EXPOSE 3000/tcp

ENTRYPOINT ["gunicorn"] 
CMD ["--bind", "0.0.0.0:3000", "--access-logfile", "-", "--error-logfile", "-", "wsgi:app"]
