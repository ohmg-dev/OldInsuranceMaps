import markdown
from bs4 import BeautifulSoup
from django import template
from django.utils.safestring import mark_safe
from slugify import slugify

register = template.Library()


@register.tag(name="markdowncontent")
def do_markdown(parser, token):
    nodelist = parser.parse(("endmarkdowncontent",))
    parser.delete_first_token()
    return MarkdownNode(nodelist)


class MarkdownNode(template.Node):
    def __init__(self, nodelist):
        self.nodelist = nodelist

    def render(self, context):
        md = markdown.Markdown(extensions=["fenced_code", "toc", "tables"])
        content = self.nodelist.render(context)
        result = mark_safe(md.convert(str(content)))
        return result


@register.tag(name="markdowntoc")
def do_markdowntoc(parser, token):
    nodelist = parser.parse(("endmarkdowntoc",))
    parser.delete_first_token()
    return MarkdownTocNode(nodelist)


class MarkdownTocNode(template.Node):
    """credit: https://stackoverflow.com/a/2515508/3873885"""

    def __init__(self, nodelist):
        self.nodelist = nodelist

    def render(self, context):
        md = markdown.Markdown()
        content = self.nodelist.render(context)
        result = mark_safe(md.convert(str(content)))
        soup = BeautifulSoup(result, features="html.parser")

        toc = []
        current_list = toc
        previous_tag = None

        for header in soup.findAll(["h2", "h3"]):
            if previous_tag == "h2" and header.name == "h3":
                current_list = []
            elif previous_tag == "h3" and header.name == "h2":
                toc.append(current_list)
                current_list = toc

            current_list.append((slugify(header.string), header.string))

            previous_tag = header.name

        if current_list != toc:
            toc.append(current_list)

        def list_to_html(lst):
            result = ["<ul>"]
            for item in lst:
                if isinstance(item, list):
                    result.append(list_to_html(item))
                else:
                    result.append('<li><a href="#{}">{}</a></li>'.format(item[0], item[1]))
            result.append("</ul>")
            return "\n".join(result)

        return list_to_html(toc)
