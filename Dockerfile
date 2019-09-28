FROM makinacorpus/geodjango:bionic-3.7

RUN mkdir /code
COPY . /code
WORKDIR /code

# Install dev requirements
RUN pip3 install -e .[dev]
