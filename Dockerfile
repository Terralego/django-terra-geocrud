FROM makinacorpus/geodjango:bionic-3.7

RUN mkdir -p /code
RUN useradd -ms /bin/bash django
COPY . /code/src
RUN chown -R django:django /code

USER django
RUN python3.7 -m venv /code/venv

WORKDIR /code/src

RUN  /code/venv/bin/pip install --no-cache-dir pip setuptools wheel -U
# Install dev requirements
RUN /code/venv/bin/pip3 install --no-cache-dir -e .[dev] -U
