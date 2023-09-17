FROM ubuntu:jammy

ENV TZ="Europe/London"
ENV NA_HOME=/usr/lib/na_api
ENV NA_VENV=$NA_HOME/venv
ENV PATH=${NA_VENV}/bin:${PATH}

RUN apt-get update && \
    apt-get install -y build-essential vim lsof git-core curl sudo jq && \
    apt-get install -y postgresql-client

# setup python
RUN apt-get install -y ghostscript libpoppler-cpp-dev pkg-config software-properties-common && \
    apt-get install -y python3-dev python3-pip python3-venv && \
    apt-get install -y libmagickwand-dev && \
    mv /etc/ImageMagick-6/policy.xml /etc/ImageMagick-6/policy.xml.off

RUN useradd -r -u 900 -m -c "na_api account" -d /usr/lib/na_api -s /bin/false na_api && echo "na_api:na_api" | chpasswd && adduser na_api sudo

WORKDIR $NA_VENV/src/na-api/
COPY . $NA_VENV/src/na-api/
RUN mv docker/data .

RUN chown -R na_api:na_api $NA_HOME $NA_VENV

USER na_api

RUN python3 -m venv $NA_VENV

RUN pip3 install -U --exists-action=b --force-reinstall -r requirements_tests.txt
