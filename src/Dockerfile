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
RUN git clone --depth 1 --branch next --recurse-submodules https://github.com/orangepi-xunlong/wiringOP-Python /tmp/wiringOP-Python \
	&& cd /tmp/wiringOP-Python \
	&& python3 generate-bindings.py > bindings.i \
	&& sed -i '/getGpioNum/d;/piGpioLayoutOops/d' bindings.i \
	&& sed -i 's/SWIG_Python_AppendOutput($result, PyString_FromStringAndSize((char *) $1, result));/SWIG_Python_AppendOutput($result, PyString_FromStringAndSize((char *) $1, result), 0);/' wiringpi.i \
	&& python3 setup.py install \
	&& rm -rf /tmp/wiringOP-Python

