FROM python:3.10


WORKDIR /app/

ADD pyproject.toml poetry.lock ./
RUN pip install poetry &&  \
    poetry config virtualenvs.create false && \
    poetry install --no-dev

ADD ./ ./

CMD ["python", "-m", "service"]