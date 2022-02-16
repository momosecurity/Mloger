FROM docker.io/centos/python-38-centos7:latest
WORKDIR /home/mloger
COPY .  .
USER root
WORKDIR /home/mloger/server
RUN pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple && mkdir /home/mloger/server/log/ && touch /home/mloger/server/log/debug.log
EXPOSE 8000 8081 8082
CMD ["python","app.py"]