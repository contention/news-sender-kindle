import os
import time
import datetime
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

    file.write("a {color: #000000; text-decoration: none; border-bottom: 1px dotted #666666;}")

    file.write("h1 {font-size: 2em; page-break-before:always}")
    file.write("h2 {font-size: 1.5em;}")
    file.write("h3 {font-size: 1.2em;}")
    file.write("hr {border: 1px solid #ddd;}")
    file.write(".toc-title {font-size: 1.5em; font-weight: bold; margin: 0 0 10px 0;}")
    file.write(".toc-section {font-size: 1.2em; font-weight: bold; margin: 0 0 10px 20px;}")
    file.write(".toc-item {margin: 0 0 10px 40px;}")
    file.write(".toc-trailtext {color: #666666; padding-top: 5px; font-style: italic;}")

    file.write("</style>")

    # Write the rest of the opening tags
    file.write("</head>")
    file.write("<body>")

    toc_string = ""
    content_string = ""


    with open('app/sources.json') as fp:
        sources = json.load(fp)

    # Loop through the sources
    for source in sources:
        title = source["title"]

        # Write the source title toc
        toc_string += "<div class='toc-title'><a href='#"+str(title)+"'>"+str(title)+"</a></div>"

        # Write the source title content
        content_string += "<h1 id='"+str(title)+"'>"+ str(title)+"</h1>"

        # Loop through the sections
        for section in source["sections"]:
            section_id = section["id"]
            section_title = section["title"]

            # Get data from the Guardian API
            print("Fetching data from the Guardian API for section: " + str(section_id))
            apiurl = "https://content.guardianapis.com/search?section=" + str(section_id) + "&type=article&show-fields=all&show-blocks=body&page-size=25&shouldHideAdverts=true&api-key=" + str(os.environ.get("GUARDIAN_API_KEY"))

            with urllib.request.urlopen(apiurl) as url:
                data = json.load(url)


            # Check if the response is ok
            if data["response"]["status"] == "ok":

                print("...ok!")

                # Write the section title toc
                toc_string += "<div class='toc-section'><a href='#"+str(section_id)+"'>"+str(section_title)+"</a></div>"

                # Write the section title content
                content_string += "<h2 id='"+str(section_id)+"'>"+ str(section_title)+"</h2>"

                # Loop through the articles
                for article in data["response"]["results"]:

                    # Format the date into something human readable
                    articledate = datetime.datetime.strptime(article["webPublicationDate"], "%Y-%m-%dT%H:%M:%SZ")
                    formattedarticledate = articledate.strftime("%H:%M %A %d %B %Y")

                    
                    # Write the article toc
                    toc_string += "<div class='toc-item'><a href='#"+article["id"]+"'>"+str(article["fields"]["headline"])+"</a> <small class='toc-trailtext'>"+str(article["fields"]["trailText"])+" | "+formattedarticledate +"</small></div>"
                    
                    # Add a link back to the contents
                    content_string += "<div><a href='#contents'>Back to contents</a></div>"
                    
                    # Write the article content
                    content_string += "<h3 id='"+article["id"]+"'>"+ str(article["fields"]["headline"])+"</h3>"
                    content_string += "<p><small>"+str(formattedarticledate)+"</small></p>"
                    content_string += str(article["fields"]["body"]) + "<hr />"

            else:
                # Write an error message
                print("...error!")
                toc_string += "<div class='toc-section'>Error fetching the '"+section_title+"' section</div>"

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