import os
import time
import urllib.request
import json

FILENAME="TheGuardian.html"

# Function to create an HTML file
def createhtml():

    # Open a file
    file = open("/output/" + str(FILENAME), "w")

    # Write the opening HTML tags
    file.write("<html>")
    file.write("<head>")
    file.write("<title>The Guardian</title>")

    # Write the CSS
    file.write("<style>")
    file.write("body {font-family: Arial, sans-serif;}")
    file.write("h1 {font-size: 2em; page-break-before:always}")
    file.write("h2 {font-size: 1.5em;}")
    file.write("h3 {font-size: 1.2em;}")
    file.write("hr {border: 1px solid #ddd;}")
    file.write(".toc-title {font-size: 1.5em; font-weight: bold;}")
    file.write(".toc-section {font-size: 1.2em; font-weight: bold; margin-left: 20px;}")
    file.write(".toc-item {margin-left: 40px;}")

    file.write("</style>")

    # Write the rest of the opening tags
    file.write("</head>")
    file.write("<body>")

    toc_string = ""
    content_string = ""


    with open('app/sources.json') as fp:
        sources = json.load(fp)

    for source in sources:
        title = source["title"]

        toc_string += "<div class='toc-title'><a href='#"+str(title)+"'>"+str(title)+"</a></div>"
        content_string += "<h1 id='"+str(title)+"'>"+ str(title)+"</h1>"
        for section in source["sections"]:
            section_id = section["id"]
            section_title = section["title"]

            # Get data from the Guardian API
            print("Fetching data from the Guardian API for section: " + str(section_id))
            apiurl = "https://content.guardianapis.com/search?section=" + str(section_id) + "&type=article&show-fields=all&show-blocks=body&page-size=25&shouldHideAdverts=true&api-key=" + str(os.environ.get("GUARDIAN_API_KEY"))

            with urllib.request.urlopen(apiurl) as url:
                data = json.load(url)

            if data["response"]["status"] == "ok":
                toc_string += "<div class='toc-section'><a href='#"+str(section_id)+"'>"+str(section_title)+"</a></div>"
                content_string += "<h2 id='"+str(section_id)+"'>"+ str(section_title)+"</h2>"
                for article in data["response"]["results"]:

                    toc_string += "<div class='toc-item'><a href='#"+article["id"]+"'>"+str(article["fields"]["headline"])+"</a></div>"
                    
                    content_string += "<div><a href='#contents'>Back to contents</a></div>"
                    content_string += "<h3 id='"+article["id"]+"'>"+ str(article["fields"]["headline"])+"</h3>"
                    content_string += str(article["fields"]["body"]) + "<hr />"
            else:
                content_string += "<h3>Error fetching the '"+section_title+"' section!</h3>"

            time.sleep(1)

    # Write the Table of Contents
    file.write("<h1 id='contents'>Contents</h1>")
    file.write(toc_string)
    
    # Write the content
    file.write(content_string)

    # Write the closing tags
    file.write("</body>")
    file.write("</html>")

    # Close the file
    file.close()

    print("HTML file successfully written.")
        

if __name__ == '__main__':
    createhtml()