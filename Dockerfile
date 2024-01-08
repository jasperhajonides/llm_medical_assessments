FROM python:3.11

WORKDIR /code

# Copy requirements.txt first to leverage Docker cache
COPY ./requirements.txt /code/requirements.txt

# Install the llama-cpp-python package with no cache directory
# Install all requirements in one step
RUN pip install --no-cache-dir --upgrade -v -r /code/requirements.txt


COPY ./app /code/app

CMD ["python", "app/main.py"]