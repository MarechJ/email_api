from python:3.6

WORKDIR /code
ADD . /code
RUN pip install -e .
RUN pip install gunicorn
