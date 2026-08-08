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
RUN git clone --depth 1 --branch next --recurse-submodules https://github.com/orangepi-xunlong/wiringOP-Python /tmp/wiringOP-Python \
	&& cd /tmp/wiringOP-Python \
	&& /usr/local/bin/python -c 'import sys, setuptools; print(sys.executable); print(setuptools.__version__)' \
	&& python3 generate-bindings.py > bindings.i \
	&& sed -i '/getGpioNum/d;/piGpioLayoutOops/d' bindings.i \
	&& swig -python -threads -o wiringpi_wrap.c wiringpi.i \
	&& sed -i 's/SWIG_Python_AppendOutput(resultobj, PyString_FromStringAndSize((char *) arg2, result));/SWIG_Python_AppendOutput(resultobj, PyString_FromStringAndSize((char *) arg2, result), 0);/' wiringpi_wrap.c \
	&& sed -i "s/sources += \['wiringpi.i'\]/sources += ['wiringpi_wrap.c']/" setup.py \
	&& /usr/local/bin/python setup.py install \
	&& rm -rf /tmp/wiringOP-Python

