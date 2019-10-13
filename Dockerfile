FROM alpine:3.10

RUN apk update \
    && apk upgrade \
    && apk add --no-cache \
    python3

RUN adduser -D \
    -u 1000 \
    webauth

RUN mkdir -p \
    /mnt/webauth/certs \
    /mnt/webauth/config \
    /mnt/webauth/db \
    && chown -R webauth:webauth /mnt/webauth

VOLUME /mnt/webauth

WORKDIR /opt/webauth
ADD requirements.txt .
RUN pip3 install -r requirements.txt

ADD . /opt/webauth
RUN python3 -m unittest discover -s . -p "*_test.py" &> /dev/null && echo "All unittests OK!"

USER webauth
ENTRYPOINT ["./webauth"]
CMD ["--config=/mnt/webauth/config/config.yaml", "--logging=debug", "--bootstrap"]
