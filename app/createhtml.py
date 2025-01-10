import os
import time
import urllib.request
import json

SECTION="world"

FILENAME="The Guardian | " + str(time.strftime("%Y-%m-%d %H:%M:%S") + ".html")

# Function to create an HTML file
def createhtml():

    # Open a file
    file = open("/output/" + str(FILENAME), "w")

    # Write HTML content
    file.write("<html>")
    file.write("<head>")
    file.write("<title>The Guardian</title>")
    file.write("</head>")
    file.write("<body>")

    # Get data from the Guardian API
    apiurl = "https://content.guardianapis.com/search?section=" + str(SECTION) + "&type=article&show-fields=all&show-blocks=body&page-size=25&shouldHideAdverts=true&api-key=" + str(os.environ.get("GUARDIAN_API_KEY"))
    print(apiurl)
    with urllib.request.urlopen(apiurl) as url:
        data = json.load(url)

    print(data["response"]["status"])
        
    for article in data["response"]["results"]:
        file.write("<h1>"+ str(article["fields"]["headline"])+"</h1>")
        file.write(str(article["fields"]["body"]))
    
    file.write("</body>")
    file.write("</html>")

    # Close the file
    file.close()

    print("HTML file successfully written.")
        

if __name__ == '__main__':
    createhtml()