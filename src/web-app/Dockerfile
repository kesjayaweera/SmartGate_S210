# Use the official Python Docker image
FROM python:3.9.21-bookworm

# Set the working directory inside the container
WORKDIR /SmartGate

COPY requirements.txt /SmartGate/

# Update, upgrade and install system dependencies
RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y libdbus-1-dev git neofetch && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install the required Python packages from the requirements.txt file
RUN pip install --no-cache-dir -r /SmartGate/requirements.txt

# Expose both Uvicorn (8000) & PostgreSQL (5432)
EXPOSE 8000 5432

# Start the bash
CMD ["bash"]
