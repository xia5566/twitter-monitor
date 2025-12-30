import cloudscraper # 引入绕过 403 的库
import smtplib
from email.mime.text import MIMEText
from email.header import Header
import os
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from email.utils import parsedate_to_datetime
import time
import random

# 1. 获取配置
TARGET_USER = os.environ.get("TARGET_USER")
MAIL_USER = os.environ.get("MAIL_USER")
MAIL_PASS = os.environ.get("MAIL_PASS")
RECEIVER = os.environ.get("RECEIVER")

# === 节点列表 ===
# 混合了 Nitter 和 RSSHub 的节点，增加成功率
NODES = [
    f"https://nitter.cz/{TARGET_USER}/rss",
    f"https://nitter.poast.org/{TARGET_USER}/rss",
    f"https://nitter.privacydev.net/{TARGET_USER}/rss",
    f"https://nitter.woodland.cafe/{TARGET_USER}/rss",
    f"https://nitter.x86-64-unknown-linux-gnu.zip/{TARGET_USER}/rss",
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
    # 创建一个模拟真实浏览器的 scraper
    scraper = cloudscraper.create_scraper(
        browser={
            'browser': 'chrome',
            'platform': 'windows',
            'desktop': True
        }
    )
    
    # 随机打乱节点顺序，避免总是死磕第一个
    random.shuffle(NODES)

    for url in NODES:
        print(f"🔄 正在尝试: {url} ...")
        try:
            # 使用 scraper.get 而不是 requests.get
            resp = scraper.get(url, timeout=15)
            
            if resp.status_code == 200:
                # 再次确认内容是否包含 RSS 标记
                if b"<rss" in resp.content or b"<feed" in resp.content:
                    print(f"✅ 成功连接！")
                    return resp.content
                else:
                    print(f"⚠️ 状态200但内容不对 (可能是假网页)，跳过。")
            else:
                print(f"❌ 状态码: {resp.status_code}")
                
        except Exception as e:
            # 只打印简短错误，不刷屏
            error_msg = str(e).split('(')[0]
            print(f"❌ 连接出错: {error_msg}")
            
    return None

def check_twitter():
    content = get_rss_content()
    if not content:
        print("🚨 所有节点都阵亡了。GitHub IP 可能被暂时封锁。")
        return

    try:
        root = ET.fromstring(content)
        items = root.findall(".//item")
        
        if not items:
            print("📭 未找到推文")
            return

        latest_item = items[0]
        title = latest_item.find("title").text
        link = latest_item.find("link").text
        pub_date_str = latest_item.find("pubDate").text
        
        tweet_time = parsedate_to_datetime(pub_date_str)
        now = datetime.now(tweet_time.tzinfo)
        
        # 40分钟判定
        if (now - tweet_time) < timedelta(minutes=40):
            print("🔔 发现新推文，准备发送...")
            send_email(title, link, pub_date_str)
        else:
            print(f"💤 最新推文是旧的 ({pub_date_str})，不发送。")
            
    except Exception as e:
        print(f"💥 解析出错: {e}")

if __name__ == "__main__":
    check_twitter()
