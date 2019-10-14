FROM makinacorpus/geodjango:bionic-3.7

RUN mkdir -p /code/src
RUN useradd -ms /bin/bash django
RUN python3.7 -m venv /code/venv

RUN chown -R django:django /code
COPY . /code/src

USER django
WORKDIR /code/src

RUN  /code/venv/bin/pip install --no-cache-dir pip setuptools wheel -U
# Install dev requirements
RUN /code/venv/bin/pip3 install --no-cache-dir -e .[dev] -U
