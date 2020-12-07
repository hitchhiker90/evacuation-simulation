FROM python:3.9-buster

# Inject application files
COPY server.py simulation.py config.py /srv/
COPY templates /srv/templates
COPY assets /srv/assets

# Update and install Mesa
RUN pip3 install mesa

# Set up a directory for logs
RUN cd srv && mkdir logs

# Start the application
CMD cd /srv && python3 server.py