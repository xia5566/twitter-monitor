import requests
import smtplib
from email.mime.text import MIMEText
from email.header import Header
import os
import xml.etree.ElementTree as ET

# 从 GitHub 环境变量中获取配置 (为了安全，不要把密码写在代码里)
TARGET_USER = os.environ.get("TARGET_USER")
MAIL_USER = os.environ.get("MAIL_USER")
MAIL_PASS = os.environ.get("MAIL_PASS")
RECEIVER = os.environ.get("RECEIVER")

# 使用 Nitter 的 RSS 源 (无需 API Key，无需登录)
# 如果此节点挂了，可以换 rss.nitter.net 等其他公共节点
RSS_URL = f"https://nitter.net/{TARGET_USER}/rss"

def send_email(title, link):
    mail_host = "smtp.qq.com"
    message = MIMEText(f"【新推文】\n\n{title}\n\n链接: {link}", 'plain', 'utf-8')
    message['From'] = Header("TwitterMonitor", 'utf-8')
    message['To'] = Header("User", 'utf-8')
    message['Subject'] = Header(f"{TARGET_USER} 发推了", 'utf-8')

    try:
        smtpObj = smtplib.SMTP_SSL(mail_host, 465)
        smtpObj.login(MAIL_USER, MAIL_PASS)
        smtpObj.sendmail(MAIL_USER, RECEIVER, message.as_string())
        print("邮件发送成功")
    except Exception as e:
        print(f"邮件发送失败: {e}")

def check_twitter():
    print(f"正在检查: {RSS_URL}")
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        resp = requests.get(RSS_URL, headers=headers, timeout=10)
        if resp.status_code == 200:
            # 解析 XML
            root = ET.fromstring(resp.content)
            # 获取第一条推文
            item = root.find(".//item")
            if item:
                title = item.find("title").text
                link = item.find("link").text
                # 这里不仅可以打印，实际使用时你需要接入数据库或文件
                # 来判断这条推文是否已经发送过。
                # GitHub Actions 每次运行环境是重置的，
                # 简单做法：只判断推文发布时间是否在过去 1 小时内。
                print(f"最新推文: {title}")
                # 示例：直接发送（实际建议加个去重逻辑）
                # send_email(title, link) 
        else:
            print("访问 Nitter 失败")
    except Exception as e:
        print(f"出错: {e}")

if __name__ == "__main__":
    check_twitter()