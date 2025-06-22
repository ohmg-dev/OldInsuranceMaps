import os
from argparse import Namespace


from django.conf import settings
from django.core.management.base import BaseCommand
from django.template.loader import render_to_string
from django.test.client import RequestFactory
from django.contrib.sessions.middleware import SessionMiddleware


class Command(BaseCommand):
    help = "Renders static HTML pages for 404 and 500 error pages."

    def handle(self, *args, **options):
        rf = RequestFactory()
        request = rf.get("/")
        middleware = SessionMiddleware(lambda x: None)
        middleware.process_request(request)
        request.session.save()
        request.user = Namespace(is_authenticated=False)
        for status in [404, 500]:
            content = render_to_string(f"{status}.html.template", request=request)
            outpath = os.path.join(settings.PROJECT_DIR, f"frontend/templates/{status}.html")
            with open(outpath, "w") as static_file:
                static_file.write(content)
            print(f"file saved to: {outpath}")
