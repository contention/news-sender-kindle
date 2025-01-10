import urllib.request, json

def createhtml():


    with urllib.request.urlopen("http://maps.googleapis.com/maps/api/geocode/json?address=google") as url:
        data = json.load(url)
        print(data)

    file = open("output.html", "w")

    # Write HTML content
    file.write("<html>")
    file.write("<head>")
    file.write("<title>My Webpage</title>")
    file.write("</head>")
    file.write("<body>")
    file.write("<h1>Welcome to my webpage!</h1>")
    file.write("</body>")
    file.write("</html>")

    # Close the file
    file.close()

    print("HTML file successfully written.")
        

if __name__ == '__main__':
    createhtml()