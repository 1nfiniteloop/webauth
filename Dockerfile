FROM alpine:3.12

RUN apk update \
    && apk upgrade \
    && apk add --no-cache \
        curl \
        python3 \
        py3-pip \
    && rm -r /var/cache/apk/*

RUN adduser -D \
    -u 1000 \
    webauth

RUN mkdir -p \
    /mnt/webauth/certs \
    /mnt/webauth/config \
    /mnt/webauth/db \
    && chown -R webauth:webauth /mnt/webauth

VOLUME /mnt/webauth

ARG INSTALL_PATH=/usr/lib/python3.7/site-packages/webauth
ADD . ${INSTALL_PATH}
WORKDIR ${INSTALL_PATH}

RUN pip3 install -r requirements.txt \
    && python3 -m unittest discover -s . -p "*_test.py" &> /dev/null && echo "All unittests OK!"

ARG FRONTEND_VER=1.0.0
RUN curl \
    --location \
    --silent \
    https://github.com/1nfiniteloop/webauth-frontend/releases/download/v${FRONTEND_VER}/webauth-frontend.tar.gz \
    |tar -xz -C ${INSTALL_PATH}

USER webauth
ENTRYPOINT ["./webauth"]
CMD ["--config=/mnt/webauth/config/config.yaml", "--logging=debug", "--bootstrap"]
