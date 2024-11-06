import logging

from django.shortcuts import render
from django.views import View

logger = logging.getLogger(__name__)


class PageView(View):

    def get(self, request, page):

        context_dict = {
            "params": {
                "PAGE_TITLE": page.title,
                "PAGE_NAME": 'markdown-page',
                "PARAMS": {
                    "HEADER": page.title,
                    # downstream SvelteMarkdown requires this variable to be `source`
                    "source": page.content,
                }
            }
        }

        return render(
            request,
            "index.html",
            context=context_dict
        )
