FROM python:3-slim

# Install tini and create an unprivileged user
ADD https://github.com/krallin/tini/releases/download/v0.19.0/tini /sbin/tini
RUN addgroup --gid 1001 "elg" && \
      adduser --disabled-password --gecos "ELG User,,," \
      --home /elg --ingroup elg --uid 1001 elg && \
      chmod +x /sbin/tini

# Copy in the requirements file to build the venv
COPY --chown=elg:elg requirements.txt /elg/

# Everything from here down runs as the unprivileged user account
USER elg:elg

WORKDIR /elg

# Create a Python virtual environment for the dependencies
RUN python -mvenv venv && venv/bin/pip --no-cache-dir install -r requirements.txt

# Copy in the actual app and entrypoint script - if using this file as a
# template for your own app, this is where you would copy in anything else your
# app depends on such as pre-trained model files, etc.
COPY --chown=elg:elg docker-entrypoint.sh elg_app.py /elg/

ENV WORKERS=1

ENTRYPOINT ["./docker-entrypoint.sh"]
