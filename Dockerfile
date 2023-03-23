FROM python:3-slim

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY wpsec-cli.py .

ENTRYPOINT [ "python", "./wpsec-cli.py" ]
