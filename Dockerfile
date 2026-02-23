FROM python:3.10-slim

# Install cron
RUN apt-get update && apt-get install -y cron && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY db.py ingest.py auth.py ./

# Set up the cron job to run ingest.py every hour
# The output is redirected to Docker's standard output so it shows up in `docker logs`
RUN echo "0 * * * * root cd /app && /usr/local/bin/python ingest.py > /proc/1/fd/1 2>/proc/1/fd/2" > /etc/cron.d/fitbyte-cron
RUN chmod 0644 /etc/cron.d/fitbyte-cron
RUN crontab /etc/cron.d/fitbyte-cron

# Run both cron (in foreground) and an initial ingestion on startup
CMD printenv > /etc/environment && /usr/local/bin/python ingest.py && cron -f
