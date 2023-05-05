FROM continuumio/miniconda3

RUN apt-get update \
  && apt-get install -y --no-install-recommends --no-install-suggests \
  build-essential ffmpeg
# conda update conda && \
RUN conda install -c conda-forge libsndfile -y && \
    pip install spleeter flask

    
WORKDIR /app

COPY ./requirements.txt /app
RUN pip install --no-cache-dir --requirement /app/requirements.txt

COPY . /app

CMD ["python", "separator.py"]
