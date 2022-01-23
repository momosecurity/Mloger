FROM node:14.15-alpine as frontbuilder
ARG USE_MIRROR
COPY front  /usr/src/front
WORKDIR /usr/src/front
RUN if [[ -n "$USE_MIRROR" ]] ; then npm --registry https://registry.npm.taobao.org install ; else npm install ; fi \
  && npm run build

FROM docker.io/centos/python-38-centos7:latest
WORKDIR /home/mlogger
COPY --from=frontbuilder  /usr/src/front  ./front
COPY server ./server
USER root
WORKDIR /home/mlogger/server
RUN pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple
CMD ["python","app.py"]