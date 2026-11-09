"""Small HTML tree helpers for reading the published guide pages."""

from __future__ import annotations

from html.parser import HTMLParser

VOID = {
    "area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta",
    "source", "track", "wbr",
}


class Node:
    def __init__(self, tag: str, attrs):
        self.tag = tag
        self.attrs = dict(attrs)
        self.children: list = []

    def cls(self) -> list[str]:
        return self.attrs.get("class", "").split()


class Builder(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = Node("document", {})
        self.stack = [self.root]

    def handle_starttag(self, tag, attrs):
        node = Node(tag, attrs)
        self.stack[-1].children.append(node)
        if tag not in VOID:
            self.stack.append(node)

    def handle_endtag(self, tag):
        for index in range(len(self.stack) - 1, 0, -1):
            if self.stack[index].tag == tag:
                del self.stack[index:]
                return

    def handle_startendtag(self, tag, attrs):
        self.stack[-1].children.append(Node(tag, attrs))

    def handle_data(self, data):
        if data:
            self.stack[-1].children.append(data)


def parse_html(text: str) -> Node:
    builder = Builder()
    builder.feed(text)
    builder.close()
    return builder.root


def find_first(node: Node, tag: str) -> Node | None:
    if node.tag == tag:
        return node
    for child in node.children:
        if isinstance(child, Node):
            found = find_first(child, tag)
            if found:
                return found
    return None


def text_of(node) -> str:
    if isinstance(node, str):
        return node
    return "".join(text_of(child) for child in node.children)


def normalized_text(node) -> str:
    return " ".join(text_of(node).split())
