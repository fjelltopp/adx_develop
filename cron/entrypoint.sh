#!/bin/sh
set -e

for s in $(echo $SECRET_ENVS | jq -r "to_entries|map(\"\(.key)=\(.value|tostring)\")|.[]"); do
    export $s
done

exec "$@"
