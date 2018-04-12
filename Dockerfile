FROM python:2.7

RUN apt-get update \
  && apt-get install -y nco gdal-bin

RUN mkdir /src
ADD requirements.txt /src
WORKDIR /src
RUN pip install -r requirements.txt


USER 1000:1258
CMD bash
