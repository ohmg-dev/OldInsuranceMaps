import os
import sys
import json
from argparse import Namespace
from pathlib import Path

import requests

from django.conf import settings
from django.core.management.base import BaseCommand
from django.template.loader import render_to_string
from django.test.client import RequestFactory
from django.contrib.sessions.middleware import SessionMiddleware


class Command(BaseCommand):
    help = "Perform various operations needed for configuration of the app."
    verbose = False
    python_env = Path(sys.executable).parent

    def add_arguments(self, parser):
        parser.add_argument(
            "operation",
            choices=[
                "services",
                "generate-error-pages",
                "initialize-s3-bucket",
                "get-plugins",
            ],
            help="Choose what configuration operation to run.",
        )
        parser.add_argument(
            "-d",
            "--destination",
            default=".services",
            help="Directory where generated service files will be placed.",
        )
        parser.add_argument(
            "--verbose",
            action="store_true",
            default=False,
            help="Verbose output.",
        )

    def _write_file(self, content: str, outpath: str):
        with open(outpath, "w") as o:
            o.write(content)
        return outpath

    def _resolve_var(self, name, default_value=None):
        value = getattr(settings, name, "<not in django settings>")
        if value == "<not in django settings>":
            value = os.getenv(name, default_value)
        return value

    def handle(self, *args, **options):
        self.verbose = options["verbose"]
        operation = options["operation"]

        if operation == "generate-error-pages":
            self.generate_error_pages()

        if operation == "initialize-s3-bucket":
            self.initialize_s3_bucket()

        if operation == "get-plugins":
            self.get_plugins()

        if operation == "services":
            out_dir = Path(options["destination"])
            output_files = self.create_services(destination=out_dir)

            if self.verbose:
                print(f"~~~\noutput directory: {out_dir.absolute()}")
                print(f"~~~\nfile count: {len(output_files)}")
                for f in output_files:
                    print(f.name)

    def write_file(self, file_path, content):
        with open(file_path, "w") as out:
            out.write(content)
        return os.path.abspath(file_path)

    def generate_uwsgi_ini(self):
        project_name = settings.WSGI_APPLICATION.split(".")[0]
        wsgi_file = settings.BASE_DIR / project_name / "wsgi.py"
        wsgi_application = f"{project_name}.wsgi:application"
        env_path = os.path.dirname(os.path.dirname(sys.executable))
        log_dir = self._resolve_var("LOG_DIR", settings.LOG_DIR)
        user = self._resolve_var("USER", "username")

        vars = [
            ("MEDIA_ROOT", ""),
            ("DATABASE_NAME", ""),
            ("DATABASE_USER", ""),
            ("DATABASE_PASSWORD", ""),
            ("DATABASE_HOST", ""),
            ("DATABASE_PORT", ""),
            ("DEBUG", False),
            ("DJANGO_SETTINGS_MODULE", None),
            ("SITE_HOST_NAME", ""),
            ("SITEURL", ""),
            ("LOGIN_REQUIRED_SITEWIDE", False),
            ("ALLOWED_HOSTS", []),
            ("ADMIN_EMAIL", ""),
            ("MAPBOX_API_TOKEN", None),
            ("BROKER_URL", ""),
            ("TITILER_HOST", ""),
            ("SWAP_COORDINATE_ORDER", False),
            ("ENABLE_CPROFILER", False),
            ("ENABLE_DEBUG_TOOLBAR", False),
            ("ENABLE_NEWSLETTER", False),
            ("OHMG_API_KEY", ""),
        ]

        if self._resolve_var("EMAIL_ENABLE", False) is True:
            vars += [
                ("EMAIL_ENABLE", True),
                ("DJANGO_EMAIL_BACKEND", "django.core.mail.backends.smtp.EmailBackend"),
                ("DJANGO_EMAIL_HOST", "localhost"),
                ("DJANGO_EMAIL_PORT", 587),
                ("DJANGO_EMAIL_HOST_USER", ""),
                ("DJANGO_EMAIL_HOST_PASSWORD", ""),
                ("DJANGO_EMAIL_USE_TLS", False),
                ("DJANGO_EMAIL_USE_SSL", False),
                ("DEFAULT_FROM_EMAIL", "admin@localhost"),
            ]

        env_section = ""
        for var in vars:
            value = self._resolve_var(var[0], var[1])
            env_section += f"env = {var[0]}={value}\n"

        # this one must be quoted because it could contain # (comment tag)
        secret = self._resolve_var("SECRET_KEY", "RanD0m%3cr3tK3y")
        env_section += f'env = SECRET_KEY="{secret}"'

        file_content = f"""[uwsgi]
# set socket and set its permissions
socket = {settings.BASE_DIR}/{project_name}.sock
chmod-socket = 664

# set user and group for process
uid = {user}
gid = www-data

# set log paths and daemon mode
logto = {log_dir}/uwsgi.log

pidfile = /tmp/{project_name}.pid

# set location of wsgi app
chdir = {settings.BASE_DIR}
module = {wsgi_application}

# virtual env location, not sure if both of these are needed
home = {env_path}
virtualenv = {env_path}

# env variables needed by geonode
{env_section}

# other geonode doc-recommended settings
#strict = false
#master = true
enable-threads = false
vacuum = true                        ; Delete sockets during shutdown
#single-interpreter = true
die-on-term = true                   ; Shutdown when receiving SIGTERM (default is respawn)
#need-app = true

touch-reload = {wsgi_file}
buffer-size = 32768

# process management, etc
harakiri = 60                        ; forcefully kill workers after 60 seconds
py-callos-afterfork = true           ; allow workers to trap signals

max-requests = 1000                  ; Restart workers after this many requests
max-worker-lifetime = 3600           ; Restart workers after this many seconds
reload-on-rss = 2048                 ; Restart workers after this much resident memory
worker-reload-mercy = 60             ; How long to wait before forcefully killing workers

cheaper-algo = busyness
processes = 128                      ; Maximum number of workers allowed
cheaper = 8                          ; Minimum number of workers allowed
cheaper-initial = 16                 ; Workers created at startup
cheaper-overload = 1                 ; Length of a cycle in seconds
cheaper-step = 16                    ; How many workers to spawn at a time

cheaper-busyness-multiplier = 30     ; How many cycles to wait before killing workers
cheaper-busyness-min = 20            ; Below this threshold, kill workers (if stable for multiplier cycles)
cheaper-busyness-max = 70            ; Above this threshold, spawn new workers
cheaper-busyness-backlog-alert = 16  ; Spawn emergency workers if more than this many requests are waiting in the queue
cheaper-busyness-backlog-step = 2    ; How many emergency workers to create if there are too many requests in the queue

# cron = -1 -1 -1 -1 -1 /usr/local/bin/python /usr/src/{project_name}/manage.py collect_metrics -n
"""

        return file_content

    def generate_uwsgi_service(self, ini_file_path: Path):
        user = self._resolve_var("USER", "username")
        project_name = settings.WSGI_APPLICATION.split(".")[0]

        file_content = f"""[Unit]
Description={project_name} uWSGI daemon
After=network.target

[Service]
User={user}
Group=www-data
Type=simple
EnvironmentFile={settings.BASE_DIR}/.env
ExecStart={self.python_env}/uwsgi --ini {ini_file_path.absolute()}
Restart=on-failure
RestartSec=10s

[Install]
WantedBy=multi-user.target
"""
        return file_content

    def generate_celery_service(self):
        log_dir = self._resolve_var("LOG_DIR", settings.LOG_DIR)

        file_content = f"""[Unit]
Description=Celery
After=rabbitmq-server.service
Requires=rabbitmq-server.service

[Service]
EnvironmentFile={settings.BASE_DIR}/.env
ExecStart={self.python_env}/celery \\
    -A ohmg.celeryapp:app worker \\
    --without-gossip --without-mingle \\
    -Ofair -B -E \\
    --statedb=worker.state \\
    -s celerybeat-schedule \\
    --loglevel=DEBUG \\
    --logfile={log_dir}/celery.log \\
    --concurrency=10 -n worker1@%h
Restart=always

[Install]
WantedBy=multi-user.target
"""

        return file_content

    def create_services(self, destination: Path):
        destination.mkdir(exist_ok=True)
        cs_path = Path(destination, "celery.service")
        self._write_file(self.generate_celery_service(), cs_path)

        ui_path = Path(destination, "uwsgi.ini")
        self._write_file(self.generate_uwsgi_ini(), ui_path)

        us_path = Path(destination, "uwsgi.service")
        self._write_file(self.generate_uwsgi_service(ui_path), us_path)

        print(f"""services created. to deploy, run the following commands:

# update celery 
sudo ln -sf {cs_path.absolute()} /etc/systemd/system
sudo systemctl daemon-reload
sudo systemctl restart celery

# update uwsgi
sudo ln -sf {us_path.absolute()} /etc/systemd/system
sudo systemctl daemon-reload
sudo systemctl restart uwsgi
""")

        return [cs_path, ui_path, us_path]

    def generate_error_pages(self):
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

    def initialize_s3_bucket(self):
        import boto3

        bucket_name = settings.S3_BUCKET_NAME
        client = boto3.client(
            "s3",
            aws_access_key_id=settings.S3_ACCESS_KEY_ID,
            aws_secret_access_key=settings.S3_SECRET_ACCESS_KEY,
            endpoint_url=settings.S3_ENDPOINT_URL,
            region_name=settings.S3_REGION,
        )

        ## create bucket if it doesn't exist
        response = client.list_buckets()
        if bucket_name not in [i["Name"] for i in response["Buckets"]]:
            print(f"Creating bucket: {bucket_name}")
            client.create_bucket(Bucket=bucket_name)
            print("Bucket created.")
        else:
            print(f"Bucket already exists: {bucket_name}")
            c = input(
                "Do you want to overwrite this bucket's "
                "CORS configuration and access policy? y/N "
            )
            if not c.lower().startswith("y"):
                exit()

        ## set CORS
        cors_configuration = {
            "CORSRules": [
                {
                    "AllowedHeaders": ["*"],
                    "AllowedMethods": ["GET"],
                    "AllowedOrigins": ["*"],
                    "ExposeHeaders": [
                        "x-amz-server-side-encryption",
                        "x-amz-request-id",
                        "x-amz-id-2",
                    ],
                    "MaxAgeSeconds": 3000,
                }
            ]
        }
        client.put_bucket_cors(Bucket=bucket_name, CORSConfiguration=cors_configuration)
        print("CORS configured:")
        print(json.dumps(cors_configuration, indent=2))

        ## set bucket policy
        bucket_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "PublicRead",
                    "Effect": "Allow",
                    "Principal": "*",
                    "Action": ["s3:GetObject"],
                    "Resource": f"arn:aws:s3:::{bucket_name}/*",
                }
            ],
        }

        # Set the new policy
        client.put_bucket_policy(
            Bucket=bucket_name,
            # Convert the policy from JSON dict to string
            Policy=json.dumps(bucket_policy),
        )
        print("Bucket policy updated:")
        print(json.dumps(bucket_policy, indent=2))

    def get_plugins(self):
        dest = Path("ohmg/frontend/static/plugins")
        dest.mkdir(exist_ok=True)

        for url in settings.PLUGIN_ASSETS:
            response = requests.get(url)
            print(url)
            with open(Path(dest, url.split("/")[-1]), mode="wb") as file:
                file.write(response.content)
