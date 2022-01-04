# 通用黑名单配置
import re

file_type_black_list = (
    '.zip', '.apk', '.mp4', '.mp3', '.rar', '.tar.gz', '.exe', '.gif', '.jpg', '.png', '.ico', '.css', '.woff', '.svg',
    '.pdf', '.patch', '.webpp', '.webp', '.svga')

domain_black_list = ('google.com', 'firefox.com')


# URL remove duplicates
def replaceD(path):
    # 替换以数字结尾
    path = re.sub(r'/([\-\._]?(\d+)[\-\._]?)+$', r'/d+', path)
    # 替换path中数字
    path = re.sub(r'/([\-\._]?(\d+)[\-\._]?)+/', r'/d+/', path)
    return path
