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
	&& /usr/local/bin/python -c 'from pathlib import Path; import re,sys; p=Path("wiringpi_wrap.c"); s=p.read_text(); s2,n=re.subn(r"SWIG_Python_AppendOutput\s*\(\s*resultobj\s*,\s*PyString_FromStringAndSize\s*\(\s*\(char \*\)\s*arg2\s*,\s*result\s*\)\s*\)", "SWIG_Python_AppendOutput(resultobj, PyString_FromStringAndSize((char *) arg2, result), 0)", s); print(f"Patched SWIG_Python_AppendOutput call(s): {n}"); n or sys.exit("Failed to patch SWIG_Python_AppendOutput call in wiringpi_wrap.c"); p.write_text(s2)' \
	&& sed -i "s/sources += \['wiringpi.i'\]/sources += ['wiringpi_wrap.c']/" setup.py \
	&& /usr/local/bin/python setup.py install \
	&& rm -rf /tmp/wiringOP-Python

