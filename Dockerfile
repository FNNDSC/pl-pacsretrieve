# Docker file for the pacsretrieve

FROM fnndsc/ubuntu-python3:latest
MAINTAINER fnndsc "dev@babymri.org"

ENV APPROOT="/usr/src/pacsretrieve"  VERSION="1.1.0"
COPY ["pacsretrieve", "${APPROOT}"]
COPY ["requirements.txt", "${APPROOT}"]

WORKDIR $APPROOT

RUN apt-get update -y\
  && apt-get install -y dcmtk imagemagick\
  && pip install -r requirements.txt

CMD ["pacsretrieve.py", "--json"]
