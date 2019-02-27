# Put together using resources from...
# https://firefart.at/post/docker_and_cron_jobs/

FROM alpine:latest

RUN apk --no-cache add bash curl jq

ENV APP_USER adxuser

RUN adduser -g "App User" -D $APP_USER

COPY crontab /var/spool/cron/crontabs/$APP_USER

COPY entrypoint.sh /usr/local/bin/entrypoint.sh

RUN chmod 0600 /var/spool/cron/crontabs/$APP_USER && \
    chmod +x /usr/local/bin/entrypoint.sh

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]

CMD ["crond", "-f", "-d", "8"]
