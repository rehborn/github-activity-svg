FROM python:3.10-slim

ENV PYTHONUNBUFFERED 1

# pipenv working directory
ENV WORKON_HOME /root
ENV PIPENV_PIPFILE /app/Pipfile

COPY Pipfile Pipfile.lock main.py /app/

WORKDIR /app

RUN pip install pipenv
RUN pipenv install --deploy

EXPOSE 8000

ENV WORK_DIR /data

ENTRYPOINT ["pipenv", "run", "python", "/app/main.py", "--work-dir", "${WORK_DIR}"]
