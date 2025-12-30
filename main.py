import requests
import smtplib
from email.mime.text import MIMEText
from email.header import Header
import os
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from email.utils import parsedate_to_datetime
import time

# 1. 获取配置
TARGET_USER = os.environ.get("TARGET_USER")
MAIL_USER = os.environ.get("MAIL_USER")
MAIL_PASS = os.environ.get("MAIL_PASS")
RECEIVER = os.environ.get("RECEIVER")

# === 核心升级：备用节点列表 (车轮战) ===
# 如果一个挂了，代码会自动尝试下一个
NITTER_NODES = [
    "https://nitter.cz",
    "https://nitter.poast.org",
    "https://nitter.privacydev.net",
    "https://nitter.projectsegfau.lt",
    "https://nitter.eu.projectsegfau.lt"
]

def send_email(title, link, pub_date):
    mail_host = "smtp.qq.com"
    content = f"时间: {pub_date}\n\n内容: {title}\n\n链接: {link}"
    message = MIMEText(content, 'plain', 'utf-8')
    message['From'] = Header("TwitterMonitor", 'utf-8')
    message['To'] = Header("User", 'utf-8')
    message['Subject'] = Header(f"【新推文】{TARGET_USER} 更新了", 'utf-8')

    try:
        smtpObj = smtplib.SMTP_SSL(mail_host, 465)
        smtpObj.login(MAIL_USER, MAIL_PASS)
        smtpObj.sendmail(MAIL_USER, RECEIVER, message.as_string())
        print(f"✅ 邮件已发送: {title}")
    except Exception as e:
        print(f"❌ 邮件发送失败: {e}")

def get_rss_content():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    # 循环尝试所有节点
    for base_url in NITTER_NODES:
        rss_url = f"{base_url}/{TARGET_USER}/rss"
        print(f"🔄 正在尝试节点: {base_url} ...")
        
        try:
            resp = requests.get(rss_url, headers=headers, timeout=10)
            if resp.status_code == 200:
                # 检查是不是真的 XML 数据 (防止返回网页验证码)
                if b"<rss" in resp.content or b"<feed" in resp.content:
                    print(f"✅ 成功连接到: {base_url}")
                    return resp.content
                else:
                    print(f"⚠️ 节点 {base_url} 返回了非 RSS 数据 (可能是验证码)，跳过。")
            else:
                print(f"❌ 节点 {base_url} 返回状态码: {resp.status_code}")
        except Exception as e:
            print(f"❌ 连接 {base_url} 出错: {e}")
            
    return None

def check_twitter():
    content = get_rss_content()
    if not content:
        print("🚨 所有 Nitter 节点都尝试失败，本次任务结束。")
        return

    try:
        root = ET.fromstring(content)
        items = root.findall(".//item")
        
        if not items:
            print("📭 未找到任何推文")
            return

        # 获取最新的一条推文
        latest_item = items[0]
        title = latest_item.find("title").text
        link = latest_item.find("link").text
        pub_date_str = latest_item.find("pubDate").text
        
        # 解析时间
        tweet_time = parsedate_to_datetime(pub_date_str)
        now = datetime.now(tweet_time.tzinfo)
        
        # 判断时间：只发送最近 40 分钟内的
        if (now - tweet_time) < timedelta(minutes=40):
            print("🔔 发现新推文，准备发送...")
            send_email(title, link, pub_date_str)
        else:
            print(f"💤 最新推文发布于 {pub_date_str}，属于旧消息，不发送。")
            
    except Exception as e:
        print(f"💥 解析 XML 出错: {e}")

if __name__ == "__main__":
    check_twitter()
