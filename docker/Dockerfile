FROM ubuntu:bionic

# RUN add-apt-repository ppa:deadsnakes/ppa && \
RUN apt-get update && \
    apt-get install -y build-essential && \
    apt-get install -y git-core

    # setup python
RUN apt-get install -y postgresql postgresql-contrib && \
    apt-get install -y ghostscript && \
    apt-get install -y libpoppler-cpp-dev pkg-config python-dev software-properties-common && \
    # apt-get install -y python-virtualenv python3.7 python3 python3.7-dev python3.7-gdbm && \
    apt-get install -y libmagickwand-dev && \
    mv /etc/ImageMagick-6/policy.xml /etc/ImageMagick-6/policy.xml.off
