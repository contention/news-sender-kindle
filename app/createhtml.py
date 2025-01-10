from typing import List
from xml.dom.minidom import getDOMImplementation, Document


def getDOM() -> Document:
    impl = getDOMImplementation()
    dt = impl.createDocumentType(
        "html",
        "-//W3C//DTD XHTML 1.0 Strict//EN",
        "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd",
    )
    return impl.createDocument("http://www.w3.org/1999/xhtml", "html", dt)


def ul(items: List[str]) -> str:
    dom = getDOM()
    html = dom.documentElement
    ul = dom.createElement("ul")
    for item in items:
        li = dom.createElement("li")
        li.appendChild(dom.createTextNode(item))
        ul.appendChild(li)
    html.appendChild(ul)
    return dom.toxml()


if __name__ == "__main__":
    print(ul(["first item", "second item", "third item"]))