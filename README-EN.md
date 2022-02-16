# Mloger
`HTTP/HTTPS/websocket/tcp` `Debugging Proxy` `Replay attack` `Security testing` 
[中文](/README.md)

## Introduction
**Mloger** is a security testing platform developed on top of **mitmproxy**. It's a lightweight version of mloger used by MOMO internal security team.
Compared to burp, this also supports socks5 proxy for TCP protocol, TCP protocol is commonly used in scenarios such as instant messaging and gaming. The functions of debugging proxy and replay for HTTP/HTTPS protocol are the same compared to burp.

## Tech stack
This project is developed on python3.8 environment

| Front-end   | Back-end   | Database           | Proxy        |
|:-----|:------|---------------|-----------|
| vue2 | Flask | mongodb、redis | mitmproxy |

## Deploy
## Docker deploy
1. Create a database directory for persistent data storage  
Changing the directory requires modifying the `docker-comemess.yml` synchronously.
```
mkdir /tmp/mongo
mkdir /tmp/redis
```
2. Start the docker
```
docker-compose up
```

## Manual deploy
### Front-end build [Optional]
After modifying the front-end source code, you need to build it. If no modification is made, skip it.
```
cd front
npm install
npm run build
```

### Back-end configuration
1. Installing mongodb and redis  
- Make sure you have config the password for redis when installation
- Creeate a database for users after the installation for mongodb
```mongo shell
use mloger
db.createUser({user:"mloger",pwd:"mloger_pwd",roles:[{"role":"readWrite","db":"mloger"}]})
```
2. Clone the project and install dependencies for the application
```bash
cd server
pip3 install -r requirements.txt
```
3. Database configuration
- You will need to config the parameters including host, port, user, password, and the name of the database in the config file `server/db/mongo_db.py` for MongoDB.
  
- You will also need to config the parameters including host, port, user, and password of the database in the config file `server/db/redis_db.py` for Redis.

-  Add system environment variables for the database configs by `echo "export PROJECT_ENV=local" >> ~/.bash_profile` in order to use.
  
- Create an Index for mongodb
```bash
mongo mongodb://mloger:mloger_pwd@localhost:27017/mloger server/db/mongo_create_indexes.js
```
4. Proxy config [Optional]  
You can check the configs for HTTP, socks, and port in `server/config/config.ini` and make sure the port is not currently used.
5. Starting the back-end
```bash
python3 app.py
```

You should be able to access the web page with IP:8000 if successful.
![img.png](front/src/assets/screenshot/首页.png)

## Usage
Reference to [User Guide](front/src/assets/usage.md)。

## About us

> 陌陌安全致力于以务实的工作保障陌陌旗下所有产品及亿万用户的信息安全，以开放的心态拥抱信息安全机构、团队与个人之间的共赢协作，以自由的氛围和丰富的资源支撑优秀同学的个人发展与职业成长。

MOMO Security Emergency Response Center：https://security.immomo.com

Our WeChat:<br>
<img src="https://momo-mmsrc.oss-cn-hangzhou.aliyuncs.com/img-1c96a083-7392-3b72-8aec-bad201a6abab.jpeg" width="200" hegiht="200" align=center /><br>
