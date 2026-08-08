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
RUN /usr/local/bin/python -m pip install -r /app/requirements.txt
RUN /usr/local/bin/python -m pip install --upgrade pip setuptools wheel
COPY ./install-wiringop-python.sh /tmp/install-wiringop-python.sh
RUN chmod +x /tmp/install-wiringop-python.sh \
	&& PYTHON_BIN=/usr/local/bin/python /tmp/install-wiringop-python.sh \
	&& rm -f /tmp/install-wiringop-python.sh

