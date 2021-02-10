FROM python:3.7-slim

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
# Download English model for spaCy
RUN python -mvenv venv \
  && venv/bin/pip --no-cache-dir install -r requirements.txt \
  && venv/bin/python -m spacy download en_core_web_sm

# Install some tools for diagnostics
#USER root
#RUN apt-get update \
#  && DEBIAN_FRONTEND=noninteractive apt-get install -y \
#    curl \
#    iputils-ping \
#    mlocate \
#    net-tools \
#    procps \
#    wget \
#  && apt-get clean \
#  && rm -rf /var/lib/apt/lists/* \
#  && updatedb
#USER 1001

# Copy in the actual app and entrypoint script - if using this file as a
# template for your own app, this is where you would copy in anything else your
# app depends on such as pre-trained model files, etc.
COPY --chown=elg:elg docker-entrypoint.sh elg_app.py /elg/
COPY --chown=elg:elg detokenizer.py dsh_annotator.py lexical_annotator.py token_sequence_annotator.py /elg/
COPY --chown=elg:elg doc /elg/doc
COPY --chown=elg:elg examples /elg/examples
COPY --chown=elg:elg resources /elg/resources

ENV WORKERS=1

ENTRYPOINT ["./docker-entrypoint.sh"]
