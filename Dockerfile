FROM python:3.9-buster

# Inject application files
COPY server.py simulation.py config.py /srv/
COPY templates /srv/templates
COPY assets /srv/assets
COPY logs /srv/logs

# Update and install Mesa
RUN pip3 install mesa
