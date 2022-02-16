# Mloger
`HTTP/HTTPS/websocket/tcp` `抓包` `重放` `安全测试` 
[English](/README-EN.md)
## 简介
**Mloger**是基于**mitmproxy**开发的安全测试平台，为陌陌安全内部mloger的开源简化版本，用于各业务线安全测试工作。  
相较于burp，本项目支持socks5代理用于测试tcp协议，tcp协议常见于im通信和游戏场景。http/https协议的抓包与重放功能与burp基本一致。

## 技术栈
本项目在python3.8环境下完成

| 前端   | 服务端   | 数据库           | 代理        |
|:-----|:------|---------------|-----------|
| vue2 | Flask | mongodb、redis | mitmproxy |

## 部署
## docker部署
1. 创建数据库目录，用于数据持久化存储  
更换目录需要同步修改`docker-compose.yml`文件
```
mkdir /tmp/mongo
mkdir /tmp/redis
```
2. 启动docker
```
docker-compose up
```

## 手动部署
### 编译前端[可选]
修改前端源码后需要再次编译，若无修改可跳过。
```
cd front
npm install
npm run build
```

### 配置服务端
1. 安装mongodb、redis  
- 安装redis时需注意添加密码后启动
- 安装mongodb后进入交互式shell，创建数据库并为其创建用户
```mongo shell
use mloger
db.createUser({user:"mloger",pwd:"mloger_pwd",roles:[{"role":"readWrite","db":"mloger"}]})
```
2. 克隆到本地并安装依赖  
```bash
cd server
pip3 install -r requirements.txt
```
3. 配置数据库账号密码  
- 你需要在`server/db/mongo_db.py`中配置本地和线上mongodb的host、port、user、password、db字段。
- 你需要在`server/db/redis_db.py`中配置本地和线上redis的host、port、password字段。
- 并且通过`echo "export PROJECT_ENV=local" >> ~/.bash_profile`在本地环境变量中增加标识字段以使用本地数据库配置。
- 创建mongodb索引
```bash
mongo mongodb://mloger:mloger_pwd@localhost:27017/mloger server/db/mongo_create_indexes.js
```
4. 配置代理[可选]  
你可以在`server/config/config.ini`中配置是否开启http、socks代理及其端口号，并保证相关端口未被占用。
5. 启动服务端
```bash
python3 app.py
```
如果一切顺利的话，那么你可以在该ip的8000端口看到web页面了。
![img.png](front/src/assets/screenshot/首页.png)

## 使用
可以参考[使用手册](front/src/assets/usage.md)。

## 关于我们

> 陌陌安全致力于以务实的工作保障陌陌旗下所有产品及亿万用户的信息安全，以开放的心态拥抱信息安全机构、团队与个人之间的共赢协作，以自由的氛围和丰富的资源支撑优秀同学的个人发展与职业成长。

陌陌安全应急响应中心：https://security.immomo.com

微信公众号:<br>
<img src="https://momo-mmsrc.oss-cn-hangzhou.aliyuncs.com/img-1c96a083-7392-3b72-8aec-bad201a6abab.jpeg" width="200" hegiht="200" align=center /><br>