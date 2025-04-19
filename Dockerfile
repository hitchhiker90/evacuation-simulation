FROM python:3.12-bookworm

# Inject application files
COPY requirements.txt /
COPY server.py simulation.py config.py /srv/
COPY templates /srv/templates
COPY assets /srv/assets

# Update and install Mesa
RUN pip install -r requirements.txt

# Set up a directory for logs
RUN cd srv && mkdir logs

# Start the application
CMD cd /srv && python3 server.py