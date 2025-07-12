from django import template
from django.utils.safestring import mark_safe

import markdown

register = template.Library()


@register.tag(name="render_markdown")
def do_markdown(parser, token):
    nodelist = parser.parse(("endmarkdownblock",))
    parser.delete_first_token()
    return MarkdownNode(nodelist)


class MarkdownNode(template.Node):
    def __init__(self, nodelist):
        self.nodelist = nodelist

    def render(self, context):
        md = markdown.Markdown(extensions=["fenced_code"])
        content = self.nodelist.render(context)
        result = mark_safe(md.convert(str(content)))
        return result
