FROM minio/minio:latest

COPY init-buckets.sh /usr/local/bin/init-buckets.sh
RUN chmod +x /usr/local/bin/init-buckets.sh

RUN mkdir -p /data

EXPOSE 9000 9001

CMD ["minio", "server", "/data", "--console-address", ":9001"]
