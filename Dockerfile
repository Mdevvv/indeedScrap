# docker build -t n8n-python .
# docker run -it --rm --name n8n -p 5678:5678 -v ~/.n8n:/home/node/.n8n n8n-python

# Use n8n image with Python already installed
FROM naskio/n8n-python:latest

# Switch to root user to install packages
USER root

# Copy requirements.txt file
COPY requirements.txt /data/requirements.txt

# Copy Python script
COPY indeedScrap.py /data/indeedScrap.py

# Install Python packages from requirements.txt
RUN pip3 install --no-cache-dir -r /data/requirements.txt

# Give node user permissions on /data directory
RUN chown -R node:node /data && chmod -R 755 /data

# Create .n8n directory with proper permissions
RUN mkdir -p /home/node/.n8n && chown -R node:node /home/node/.n8n

# Stay as root user to avoid su-exec issues
# USER node

# Set environment variable to run n8n as root
ENV N8N_USER_FOLDER=/home/node/.n8n

# Expose n8n default port
EXPOSE 5678

# Start n8n
CMD ["n8n"]

# Start n8n
CMD ["n8n"]