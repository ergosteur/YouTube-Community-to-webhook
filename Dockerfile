# Use an official Python runtime as a parent image
FROM python:3

# Set the working directory in the container
WORKDIR /usr/src/app

# Install any needed packages specified in requirements.txt
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy the script into the container at /usr/src/app
COPY ytcommunity-to-webhook.py .

# Run ytcommunity-to-webhook.py when the container launches and every 10 minutes
CMD while true; do python ytcommunity-to-webhook.py; sleep 600; done
