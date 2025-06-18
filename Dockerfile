FROM python:3-slim

# Create a non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

WORKDIR /usr/src/app

# Copy and install requirements as root (needed for pip install)
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY wpsec-cli.py .

# Change ownership of the working directory to the non-root user
RUN chown -R appuser:appuser /usr/src/app

# Switch to non-root user
USER appuser

ENTRYPOINT [ "python", "./wpsec-cli.py" ]