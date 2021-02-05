#!/bin/sh

exec /sbin/tini -- venv/bin/gunicorn --bind=0.0.0.0:8000 "--workers=$WORKERS" --worker-tmp-dir=/dev/shm "$@" elg_app:app --capture-output --log-level debug --error-logfile gunicorn.error.log --access-logfile gunicorn.log
