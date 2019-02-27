# Put together using resources from...
# https://firefart.at/post/docker_and_cron_jobs/

FROM alpine:latest

ENV APP_USER adxuser

RUN adduser -g "App User" -D $APP_USER

COPY crontab /var/spool/cron/crontabs/$APP_USER

RUN chmod 0600 /var/spool/cron/crontabs/$APP_USER

ENTRYPOINT "crond"

CMD ["-f", "-d", "8"]
