FROM docker.io/zauberzeug/nicegui:latest

USER root
RUN apt update && apt install -y --no-install-recommends \
	build-essential \
	git \
	swig \
	python3-dev \
	python3-setuptools \
	&& rm -rf /var/lib/apt/lists/*

ENTRYPOINT /usr/local/bin/python -u main.py

COPY ../requirements.txt /app
RUN pip install -r /app/requirements.txt
RUN pip install git+https://github.com/orangepi-xunlong/wiringOP-Python@next

