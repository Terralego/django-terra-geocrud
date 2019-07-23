FROM makinacorpus/geodjango:bionic-3.7

RUN mkdir /code
COPY . /code
WORKDIR /code

RUN python3.7 setup.py install
