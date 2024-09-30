#!/usr/bin/env python
# encoding: utf-8

# https://www.reddit.com/r/selfhosted/comments/1aoz6pv/selfhosted_python_news_sender_script_to_kindle/

# Pseudocode
# Need to run this as a cron job at 6am, 12pm, 6pm and 9pm.
# Pull the RSS feeds from the list of feeds.
# Get the posts from the feeds since the last time the feeds were pulled. If it's the first time, get all posts.
# Create an epub file with the posts.
# Send the epub file to the kindle email.
# Delete the epub file.
# Update a system variable with the last time the feeds were pulled.


# PYTHON boilerplate
from email.utils import COMMASPACE, formatdate
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
import smtplib
import morss
import sys
import pypandoc
import pytz
from tzlocal import get_localzone
import time
import logging
import threading
import subprocess
from datetime import datetime, timedelta, timezone
import os
import feedparser
from FeedparserThread import FeedparserThread
from PIL import Image, ImageDraw, ImageFont

logging.basicConfig(level=logging.INFO)

EMAIL_SMTP = os.getenv("EMAIL_SMTP")
EMAIL_SMTP_PORT = int(os.getenv("EMAIL_SMTP_PORT"))
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASSWD = os.getenv("EMAIL_PASSWORD")
EMAIL_FROM = os.getenv("EMAIL_FROM")
KINDLE_EMAIL = os.getenv("KINDLE_EMAIL")
PANDOC = os.getenv("PANDOC_PATH", "/usr/bin/pandoc")

PERIOD = int(os.getenv("UPDATE_PERIOD", 8))  # hours between RSS pulls
FETCH_PERIOD=int(os.getenv("FETCH_PERIOD",8))
ENCRYPTION = os.getenv("ENCRYPTION")

FEED_FILE = '/config/feeds.txt'
COVER_FILE = '/cover.png'

RUN_TIMES = [(6, 0), (14, 0), (22, 0)]

SEND_EMAIL = True

feed_file = os.path.expanduser(FEED_FILE)

os.environ['TZ'] = 'Europe/London'


def create_cover(time):
    now = datetime.now()
    local_tz = get_localzone()
    timereadable = now.astimezone(local_tz).strftime("%H:%M%p\n%A %d %B \n%Y")
    img = Image.new('RGB', (600, 800), color = (73, 109, 137))
    largefont = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 100, encoding="unic")
    smallfont = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 35, encoding="unic")
    cover = ImageDraw.Draw(img)
    cover.text((50,50), f"News", font=largefont, fill=(255,255,0))
    cover.text((50,175), f"{timereadable}", font=smallfont, fill=(255,255,0))
    img.save(COVER_FILE)
   


def load_feeds():
    """Return a list of the feeds for download.
        At the moment, it reads it from `feed_file`.
    """
    with open(feed_file, 'r') as f:
        return list(f)


# Get all posts from the feeds
def get_posts_list(feed_list, START):
    """
    Spawn a worker thread for each feed.
    """
    posts = {}
    ths = []
    lock = threading.Lock()

    def append_posts(blog, new_posts):
        lock.acquire()
        if blog not in posts:
            posts[blog] = []
    
        new_posts.reverse()

        posts[blog].extend(new_posts)
        logging.info(f"Downloaded {len(new_posts)} posts from {blog}")
        
        lock.release()

    for link in feed_list:
        url = str(link)
        options = morss.Options(format='rss')
        url, rss = morss.FeedFetch(url, options)
        rss = morss.FeedGather(rss, url, options)
        output = morss.FeedFormat(rss, options, 'unicode')
        feed = feedparser.parse(output)
        th = FeedparserThread(feed, START, append_posts)
        ths.append(th)
        th.start()

    for th in ths:
        th.join()

    # When all is said and done,
    return posts


# 
def nicedate(dt):
    return dt.strftime('%d %B %Y').strip('0')

# 
def nicehour(dt):
    return dt.strftime('%I:%M&thinsp;%p').strip('0').lower()

# 
def nicepost(post):
    thispost = post._asdict()
    thispost['nicedate'] = nicedate(thispost['time'])
    thispost['nicetime'] = nicehour(thispost['time'])
    return thispost


# <link rel="stylesheet" type="text/css" href="style.css">

html_head = u"""<html>
<meta charset="UF-8" />
<meta name="viewport" content="width=device-width" />
<head>
  <meta name="viewport" content="width=device-width, initial-scale=1.0">

  <meta name="apple-mobile-web-app-capable" content="yes" />
<style>
</style>
<title>NEWS: {nowreadable}</title>
</head>
<body>

"""

html_tail = u"""
</body>
</html>
"""

html_perpost = u"""
    <article>
        <h2>{title}</h2>
        <p><small>By {author} for <i>{blog}</i>, on {nicedate} at {nicetime}.</small></p>
         {body}
         <hr />
    </article>
"""


# Send email
def send_mail(send_from, send_to, subject, text, files):
    # assert isinstance(send_to, list)

    msg = MIMEMultipart()
    msg['From'] = send_from
    msg['To'] = COMMASPACE.join(send_to)
    msg['Date'] = formatdate(localtime=True)
    msg['Subject'] = subject
    msg.attach(MIMEText(text, 'text', 'utf-8'))

    for f in files or []:
        with open(f, "rb") as fil:
            msg.attach(MIMEApplication(
                fil.read(),
                Content_Disposition=f'attachment; filename="{os.path.basename(f)}"',
                Name=os.path.basename(f)
            ))
    if ENCRYPTION == "SSL":
        smtp = smtplib.SMTP_SSL(EMAIL_SMTP, EMAIL_SMTP_PORT)
    elif ENCRYPTION == "TLS":
        smtp = smtplib.SMTP(EMAIL_SMTP, EMAIL_SMTP_PORT)
        smtp.ehlo()
        smtp.starttls()
    else:
        sys.exit("ENCRYPTION TYPE NOT FOUND !")

    smtp.login(EMAIL_USER, EMAIL_PASSWD)
    smtp.sendmail(send_from, send_to, msg.as_string())
    smtp.quit()


def convert_ebook(input_file, output_file):
    cmd = ['ebook-convert', input_file, output_file]
    process = subprocess.Popen(cmd)
    process.wait()


# Main function
def build_document():

    # Get the current time
    now = datetime.now()
    local_tz = get_localzone()
    nowreadable = now.astimezone(local_tz).strftime("%H:%M%p on %A %d %B, %Y")
    logging.info(f"Starting at {nowreadable}...")
    

    # Get the last time the feeds were pulled

    # First check file exists
    if not os.path.exists('/lastpulled.txt'):
        lastpulledtime = now - timedelta(hours=6, minutes=0)
    else:
        with open('/lastpulled.txt', 'r') as file:
            lastpulledtime = datetime.strptime(file.read(), "%d-%b-%Y (%H:%M:%S.%f)")

    # If there is no last pulled time, set it to the current time
    if lastpulledtime is None:
        lastpulledtime = now - timedelta(hours=6, minutes=0)

    
    # Create cover image
    create_cover(now);
    
    # Get all posts from last pulled time to now
    lastpulledtimereadable = lastpulledtime.astimezone(local_tz).strftime("%H:%M%p on %A %d %B, %Y")
    logging.info(f"Collecting posts since {lastpulledtimereadable}")
    posts = get_posts_list(load_feeds(), lastpulledtime)


    if posts:
        logging.info("Compiling...")

        result = html_head.format(nowreadable=nowreadable) + \
            u"\n".join([f"<br pagebreak=\"always\"><h1>{feed_url}</h1>" + \
                        u"\n".join([html_perpost.format(**nicepost(post)) for post in feed_posts])
                        for feed_url, feed_posts in posts.items()]) + html_tail


        logging.info("Creating ePub...")
        documentname = now.astimezone(local_tz).strftime("%Y%m%d%H%M")
        epubFile = str(documentname)+'.epub'
        mobiFile = str(documentname)+'.mobi'
        os.environ['PYPANDOC_PANDOC'] = PANDOC

        pypandoc.convert_text(result,
                              to='epub3',
                              format="html",
                              outputfile=epubFile,
                              extra_args=["--standalone",
                                            f"--toc",
                                          f"--epub-cover-image={COVER_FILE}",
                                          ])
        convert_ebook(epubFile, mobiFile)
        epubFile_2 = str(documentname)+'_news.epub'
        convert_ebook(mobiFile, epubFile)

        if not SEND_EMAIL:
            logging.info("Not sending email, as SEND_EMAIL is False")
        else:
            logging.info("Sending to kindle email...")
            send_mail(send_from=EMAIL_FROM,
                    send_to=[KINDLE_EMAIL],
                    subject="News - " + nowreadable,
                    text="This is your daily news.\n\n--\n\n",
                    files=[epubFile])
            logging.info("Cleaning up...")
            os.remove(epubFile)
            os.remove(mobiFile)

    logging.info("Finished!")
    logging.info("**************************")
    
    # Set the last pulled time to the current time
    with open('/lastpulled.txt', 'w') as file:
        file.write(now.strftime("%d-%b-%Y (%H:%M:%S.%f)"))


# Main loop
if __name__ == '__main__':
    build_document()
