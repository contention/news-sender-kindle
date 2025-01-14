#!/usr/bin/env python

#TO DO
# - Improve cover image with image and date/time
# - Better error handling/logging
# - Better commenting
# - Better content styling
# - Images in articles?
# - Better README documentation
# - Better environment management
# - Enable self-containment - no need to mount a volume/build files in the container itself
# - Remove chapter keywords from article titles
# - Add a way to trigger the script ad-hoc, from a URL for example
# - add title to meta (https://manual.calibre-ebook.com/generated/en/ebook-convert.html#metadata)




from email.utils import COMMASPACE, formatdate
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
import os
import sys
import time
import datetime
import urllib.request
import json
import smtplib
import sys
import pytz
import time
import logging
import threading
import subprocess
import re
from PIL import Image, ImageDraw, ImageFont


# Configuration
ENCRYPTION = os.getenv("ENCRYPTION")
EMAIL_SMTP = os.getenv("EMAIL_SMTP")
EMAIL_SMTP_PORT = int(os.getenv("EMAIL_SMTP_PORT"))
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
EMAIL_FROM = os.getenv("EMAIL_FROM")
KINDLE_EMAIL = os.getenv("KINDLE_EMAIL")

OUTPUT_DIRECTORY = "/output/"
HTML_FILE_NAME="theguardian.html"
COVER_FILE_NAME="cover.jpg"
EPUB_FILE_NAME="theguardian.epub"
MOBI_FILE_NAME="theguardian.mobi"


# Function to return human readable time
def human_readable_time(time):
    if time is None:
        time = datetime.datetime.now()
    else:
        time = datetime.datetime.strptime(time, "%Y-%m-%dT%H:%M:%SZ")
    return time.strftime("%H:%M%p\n%A %d %B \n%Y")


# Function to create a cover image
def create_cover():
    largeFont = ImageFont.truetype("/server/assets/Poppins-Bold.ttf", 60)
    smallFont = ImageFont.truetype("/server/assets/Poppins-Bold.ttf", 40)
    img = Image.new('RGB', (600, 800), color = (90,90,90))
    cover = ImageDraw.Draw(img)
    cover.text((50,50), f"The Guardian", font=largeFont, fill=(255,255,255))
    cover.text((50,175), f"{human_readable_time(None)}", font=smallFont, fill=(255,255,255))
    img.save(str(OUTPUT_DIRECTORY) + str(COVER_FILE_NAME))


# Function to process article headers and ids
def process_chapter_words(text):
    text = text.replace("chapter", "c&ZeroWidthSpace;hapter")
    text = text.replace("book", "b&ZeroWidthSpace;ook")
    text = text.replace("section", "s&ZeroWidthSpace;ection")
    text = text.replace("prologue", "p&ZeroWidthSpace;rologue")
    text = text.replace("epilogue", "e&ZeroWidthSpace;pilogue")
    text = text.replace("part", "p&ZeroWidthSpace;art")
    return text



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

    smtp.login(EMAIL_USER, EMAIL_PASSWORD)
    smtp.sendmail(send_from, send_to, msg.as_string())
    smtp.quit()


# Function to convert an ebook
def convert_ebook(input_file, output_file):
    cmd = ['ebook-convert', input_file, output_file, "--use-auto-toc", "--cover", str(OUTPUT_DIRECTORY) + str(COVER_FILE_NAME)]
    process = subprocess.Popen(cmd)
    process.wait()


# Main function
def build():

    # Open a file
    file = open(str(OUTPUT_DIRECTORY) + str(HTML_FILE_NAME), "w")

    # Write the opening HTML tags
    file.write("<!DOCTYPE html>")
    file.write("<html>")
    file.write("<head>")
    file.write("<meta http-equiv='Content-Type' content='text/html; charset=UTF-8' />")
    file.write("<title>The Guardian: " + str(human_readable_time(None)) + "</title>")

    # Write the CSS
    file.write("<style>")
    file.write("body {font-family: Arial, sans-serif;}")

    file.write("a {color: #000000; text-decoration: none; border-bottom: 1px dotted #666666;}")

    file.write("h1 {font-size: 2em; page-break-before:always}")
    file.write("h2 {font-size: 1.5em; page-break-before:always}")
    file.write("h3 {font-size: 1.2em;}")
    file.write("hr {border: 1px solid #ddd;}")
    file.write(".toc-section {font-size: 1.5em; font-weight: bold; margin: 0 0 10px 0;}")
    file.write(".toc-item {margin: 0 0 10px 20px;}")
    file.write(".toc-trailtext {color: #666666; padding-top: 5px; font-style: italic;}")

    file.write("</style>")

    # Write the rest of the opening tags
    file.write("</head>")
    file.write("<body>")

    toc_string = ""
    content_string = ""


    with open('/server/config/sections.json') as fp:
        sections = json.load(fp)

        # Loop through the sections
        for section in sections:
            section_id = section["id"]
            section_title = section["title"]

            # Get data from the Guardian API
            print("Fetching data from the Guardian API for section: " + str(section_id))
            sys.stdout.flush()

            apiurl = "https://content.guardianapis.com/search?section=" + str(section_id) + "&type=article&show-fields=all&show-blocks=body&page-size=25&shouldHideAdverts=true&api-key=" + str(os.environ.get("GUARDIAN_API_KEY"))

            with urllib.request.urlopen(apiurl) as url:
                data = json.load(url)


            # Check if the response is ok
            if data["response"]["status"] == "ok":

                print("...ok!")
                sys.stdout.flush()

                # Write the section title toc
                toc_string += "<div class='toc-section'><a href='#"+str(section_id)+"'>"+str(section_title)+"</a></div>"

                # Write the section title content
                content_string += "<h1 class='chapter' id='"+str(section_id)+"'>" + str(section_title) + "</h1>"


                # Loop through and build section contents
                for article in data["response"]["results"]:

                    # Format the date into something human readable
                    articledate = human_readable_time(article["webPublicationDate"])


                    articledate = datetime.datetime.strptime(article["webPublicationDate"], "%Y-%m-%dT%H:%M:%SZ")
                    formattedarticledate = articledate.strftime("%H:%M %A %d %B %Y")

                    article_header = process_chapter_words(str(article["fields"]["headline"]))
                    article_id = process_chapter_words(str(article["id"]))
                    content_string += "<div class='toc-item'><a href='#"+article_id+"'>"+article_header+"</a> <small class='toc-trailtext'>"+str(article["fields"]["trailText"])+" | "+formattedarticledate +"</small></div>"


                # Loop through and add the individual article text
                for article in data["response"]["results"]:

                    # Format the date into something human readable
                    articledate = human_readable_time(article["webPublicationDate"])
                    
                    # Write the article content
                    article_header = process_chapter_words(str(article["fields"]["headline"]))
                    article_id = process_chapter_words(str(article["id"]))
                    content_string += "<h2 id='"+article_id+"'>" + article_header +"</h2>"
                    
                    # Write the author and date
                    content_string += "<p><small>"+str(formattedarticledate)+"</small></p>"

                    # Process the body text
                    bodytext = str(article["fields"]["body"]).replace("h1", "h3")
                    bodytext = bodytext.replace("h2", "h3")
                    bodytext = re.sub(r"<(?:a\b[^>]*>|/a>)", "", bodytext)
                    content_string += bodytext

                    # Add a link back to the contents
                    content_string += "<div><small><a href='#"+str(section_id)+"'>Section home</a></small></div>"

                    # Add a horizontal line to signify the end of the article
                    content_string += "<hr />"

            else:
                # Write an error message
                print("...error!")
                toc_string += "<div class='toc-section'>Error fetching the '"+section_title+"' section</div>"

            time.sleep(1)

    # Write the Table of Contents
    file.write("<h1 class='chapter' id='contents'>Contents</h1>")
    file.write(toc_string)
    
    # Write the content
    file.write(content_string)

    # Write the closing tags
    file.write("</body>")
    file.write("</html>")

    # Close the file
    file.close()

    print("HTML file successfully written.")

    # Create the cover image
    create_cover()
    
    # Convert the html to epub
    convert_ebook(str(OUTPUT_DIRECTORY) + HTML_FILE_NAME, str(OUTPUT_DIRECTORY) + EPUB_FILE_NAME)


    if os.getenv("SEND_EMAIL") == "True":
        logging.info("Sending to kindle email...")
        send_mail(send_from=EMAIL_FROM,
                send_to=[KINDLE_EMAIL],
                subject="News - ",
                text="This is your daily news.\n\n--\n\n",
                files=[str(OUTPUT_DIRECTORY) + EPUB_FILE_NAME])
        logging.info("Cleaning up...")
        #os.remove(epubFile)
        #os.remove(mobiFile)
    else:
        logging.info("Email sending is disabled. Skipping...")


if __name__ == '__main__':
    build()