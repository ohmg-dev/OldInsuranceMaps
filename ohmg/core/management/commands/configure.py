import os
import sys
from argparse import Namespace
from pathlib import Path

import requests

from django.conf import settings
from django.core.management.base import BaseCommand
from django.template.loader import render_to_string
from django.test.client import RequestFactory
from django.contrib.sessions.middleware import SessionMiddleware


class Command(BaseCommand):
    help = (
        "generate various system configuration files that incorporate the "
        "the current app settings."
    )
    out_dir = "_system-configs"
    verbose = False
    python_env = Path(sys.executable).parent

    def add_arguments(self, parser):
        parser.add_argument(
            "type",
            choices=[
                "supervisor",
                "celery",
                "uwsgi",
                #                "nginx",
                #                "nginx-ssl",
                "all",
                "generate-error-pages",
                "initialize-s3-bucket",
                "get-plugins",
                "services",
            ],
            nargs="+",
            help="Choose what configurations to generate.",
        )
        parser.add_argument(
            "-d",
            "--directory",
            help="Directory where the generated files will be placed.",
        )
        parser.add_argument(
            "--cert-file",
            help="Full path to the SSL certificate to be used in the nginx config",
        )
        parser.add_argument(
            "--deploy",
            action="store_true",
            default=False,
            help="Attempts to deploy the new settings to system locations.",
        )
        parser.add_argument(
            "--verbose",
            action="store_true",
            default=False,
            help="Verbose output.",
        )

    def _write_file(self, content: str, filename: str):
        Path(self.out_dir).mkdir(exist_ok=True)
        outpath = Path(self.out_dir, filename)
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
        create_all = "all" in options["type"]

        if options["directory"] is not None:
            self.out_dir = os.path.abspath(options["directory"])

        if not os.path.isdir(self.out_dir):
            os.mkdir(self.out_dir)

        outputs = []
        if create_all or "supervisor" in options["type"]:
            if self.verbose:
                print("creating supervisord service")
            s_file = self.write_supervisor_config()
            outputs.append(s_file)

            ds_file = self.write_supervisor_deploy(s_file)
            outputs.append(ds_file)

        if create_all or "celery" in options["type"]:
            if self.verbose:
                print("creating celery config")
            c_file = self.write_project_celery_config()
            outputs.append(c_file)

            dc_file = self.write_celery_deploy(c_file)
            outputs.append(dc_file)

        if create_all or "uwsgi" in options["type"]:
            if self.verbose:
                print("creating uwsgi ini and service configs")
            ini_file = self.write_project_uwsgi_ini()
            outputs.append(ini_file)

            us_file = self.write_uwsgi_service(ini_file)
            outputs.append(us_file)

            du_file = self.write_uwsgi_service_deploy(us_file)
            outputs.append(du_file)

        if create_all or "nginx" in options["type"]:
            if self.verbose:
                print("creating nginx site config")
            nginx_site_file = self.write_nginx_site_conf()
            outputs.append(nginx_site_file)

        if create_all or "nginx-ssl" in options["type"]:
            if self.verbose:
                print("creating nginx SSL site config")
            nginx_ssl_site_file = self.write_nginx_ssl_site_conf()
            outputs.append(nginx_ssl_site_file)

        if self.verbose:
            print(f"~~~\noutput directory: {os.path.abspath(self.out_dir)}")
            print(f"~~~\nfile count: {len(outputs)}")
            for f in outputs:
                print(os.path.basename(f))

        if options["type"] == "generate-error-pages":
            self.generate_error_pages()

        if options["type"] == "initialize-s3-bucket":
            self.initialize_s3_bucket()

        if "get-plugins" in options["type"]:
            self.get_plugins()

        if "services" in options["type"]:
            self.create_services()

    def write_file(self, file_path, content):
        with open(file_path, "w") as out:
            out.write(content)

        return os.path.abspath(file_path)

    def write_supervisor_config(self):
        """
        Writes a supervisor conf file with all necessary environment variables.
        """

        vars = [
            ("DEBUG", False),
            ("SITEURL", ""),
            ("DJANGO_SETTINGS_MODULE", None),
            ("BROKER_URL", ""),
            ("DATABASE_NAME", ""),
            ("DATABASE_USER", ""),
            ("DATABASE_PASSWORD", ""),
            ("DATABASE_HOST", ""),
            ("DATABASE_PORT", ""),
            ("CACHE_DIR", ""),
            ("MEDIA_ROOT", ""),
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

        kv_list = []
        for var in vars:
            value = self._resolve_var(var[0], var[1])
            kv_list.append(f'{var[0]}="{value}"')
        env_block = "\n    " + ",\n    ".join(kv_list)

        file_content = f"""; supervisor config file

[unix_http_server]
file=/var/run/supervisor.sock   ; (the path to the socket file)
chmod=0700                       ; sockef file mode (default 0700)

[supervisord]
nodaemon=true
logfile=/var/log/supervisor/supervisord.log ; (main log file;default $CWD/supervisord.log)
pidfile=/var/run/supervisord.pid ; (supervisord pidfile;default supervisord.pid)
childlogdir=/var/log/supervisor            ; ('AUTO' child log dir, default $TEMP)
environment={env_block}

; the below section must remain in the config file for RPC
; (supervisorctl/web interface) to work, additional interfaces may be
; added by defining them in separate rpcinterface: sections
[rpcinterface:supervisor]
supervisor.rpcinterface_factory = supervisor.rpcinterface:make_main_rpcinterface

[supervisorctl]
serverurl=unix:///var/run/supervisor.sock ; use a unix:// URL  for a unix socket

; The [include] section can just contain the "files" setting.  This
; setting can list multiple files (separated by whitespace or
; newlines).  It can also contain wildcards.  The filenames are
; interpreted as relative to this file.  Included files *cannot*
; include files themselves.

[include]
files = /etc/supervisor/conf.d/*.conf
"""

        outfile_path = os.path.join(self.out_dir, "supervisord.conf")
        full_path = self.write_file(outfile_path, file_content)

        return full_path

    def write_supervisor_deploy(self, conf_path):
        deploy_path = os.path.join(self.out_dir, "deploy-supervisor.sh")
        deploy_content = f"""#!/bin/bash
sudo cp {conf_path} /etc/supervisor/supervisord.conf

# kill celery workers and reload supervisor
sudo pkill celery -f
sudo supervisorctl reload
"""
        full_deploy_path = self.write_file(deploy_path, deploy_content)

        return full_deploy_path

    def write_project_celery_config(self):
        project_name = settings.WSGI_APPLICATION.split(".")[0]
        env_file = settings.BASE_DIR / ".env"
        user = self._resolve_var("USER", "username")
        celery_path = os.path.join(os.path.dirname(sys.executable), "celery")

        file_content = f"""[program:{project_name}-celery]
command=sh -c \'. {env_file} && {celery_path} -A {project_name}.celeryapp:app worker -B -E --loglevel=DEBUG --concurrency=10 -n worker1@%%h'
directory={settings.BASE_DIR}
user={user}
numproc=4
stdout_logfile=/var/log/{project_name}-celery.log
stderr_logfile=/var/log/{project_name}-celery.log
autostart=true
autorestart=true
startsecs=10
stopwaitsecs=600
"""

        outfile_path = os.path.join(self.out_dir, f"{project_name}-celery.conf")

        return self.write_file(outfile_path, file_content)

    def write_celery_deploy(self, celery_conf):
        deploy_path = os.path.join(self.out_dir, "deploy-celery.sh")
        deploy_content = f"""#!/bin/bashtop_dir
sudo ln -sf {celery_conf} /etc/supervisor/conf.d/{os.path.basename(celery_conf)}

# Restart supervisor
sudo pkill celery -f
sudo supervisorctl reload
"""
        full_deploy_path = self.write_file(deploy_path, deploy_content)

        return full_deploy_path

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

    def write_project_uwsgi_ini(self):
        outfile_path = os.path.join(self.out_dir, "uwsgi.ini")

        file_content = self.generate_uwsgi_ini()
        return self.write_file(outfile_path, file_content)

    def write_uwsgi_service(self, ini_file="<UPDATE WITH PATH TO .ini FILE>"):
        uwsgi_path = os.path.join(os.path.dirname(sys.executable), "uwsgi")
        user = self._resolve_var("USER", "username")
        project_name = settings.WSGI_APPLICATION.split(".")[0]

        file_content = f"""[Unit]
Description={project_name} uWSGI daemon
After=network.target

[Service]
User={user}
Group=www-data
Type=simple
ExecStart=/bin/bash -c '{uwsgi_path} --ini {ini_file}'
Restart=on-failure
RestartSec=10s

[Install]
WantedBy=multi-user.target
"""

        outfile_path = os.path.join(self.out_dir, "uwsgi.service")

        return self.write_file(outfile_path, file_content)

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
ExecStart={self.python_env}/uwsgi --ini {ini_file_path.absolute()}
Restart=on-failure
RestartSec=10s

[Install]
WantedBy=multi-user.target
"""
        return file_content

    def write_uwsgi_service_deploy(self, service_file):
        deploy_path = os.path.join(self.out_dir, "deploy-uwsgi-service.sh")
        service_name = os.path.splitext(os.path.basename(service_file))[0]
        deploy_content = f"""#!/bin/bash
sudo ln -sf {service_file} /etc/systemd/system

# refresh service
sudo systemctl daemon-reload
sudo systemctl stop {service_name}
sudo pkill uwsgi -f
sudo systemctl start {service_name}
"""
        full_deploy_path = self.write_file(deploy_path, deploy_content)

        return full_deploy_path

    def write_nginx_site_conf(self):
        print("not fully implemented")
        return

        SITE_HOST_NAME = self._resolve_var("SITE_HOST_NAME")
        file_name = SITE_HOST_NAME + ".conf"

        MEDIA_ROOT = self._resolve_var("MEDIA_ROOT")
        MEDIA_URL = self._resolve_var("MEDIA_URL")
        MEDIA_URL_clean = MEDIA_URL.rstrip("/")

        STATIC_ROOT = self._resolve_var("STATIC_ROOT")
        STATIC_URL = self._resolve_var("STATIC_URL")
        STATIC_URL_clean = STATIC_URL.rstrip("/")

        LOCAL_ROOT = self._resolve_var("LOCAL_ROOT")
        top_dir = os.path.dirname(LOCAL_ROOT)
        project_name = os.path.basename(LOCAL_ROOT)

        file_content = f"""# {file_name}

# the upstream component nginx needs to connect to
upstream {project_name} {{
    server unix:{top_dir}/{project_name}.sock;
}}

# configuration of the server
server {{
    listen      80;
    server_name {SITE_HOST_NAME};
    charset     utf-8;

    # max upload size
    client_max_body_size 75M;   # adjust to taste

    location {MEDIA_URL_clean}  {{
        alias {MEDIA_ROOT};
    }}

    location {STATIC_URL_clean} {{
        alias {STATIC_ROOT};
    }}

    location / {{
        uwsgi_pass  {project_name};
        include     /etc/nginx/uwsgi_params;
    }}
}}
"""

        outfile_path = os.path.join(self.out_dir, file_name)

        return self.write_file(outfile_path, file_content)

    def write_nginx_ssl_site_conf(self):
        print("not fully implemented")
        return

        SITE_HOST_NAME = self._resolve_var("SITE_HOST_NAME")
        file_name = SITE_HOST_NAME + "-ssl.conf"

        MEDIA_ROOT = self._resolve_var("MEDIA_ROOT")
        MEDIA_URL = self._resolve_var("MEDIA_URL")
        MEDIA_URL_clean = MEDIA_URL.rstrip("/")

        STATIC_ROOT = self._resolve_var("STATIC_ROOT")
        STATIC_URL = self._resolve_var("STATIC_URL")
        STATIC_URL_clean = STATIC_URL.rstrip("/")

        LOCAL_ROOT = self._resolve_var("LOCAL_ROOT")
        top_dir = os.path.dirname(LOCAL_ROOT)
        project_name = os.path.basename(LOCAL_ROOT)

        ## attempt to find LE cert for this domain
        fullchain_path = f"/etc/letsencrypt/live/{SITE_HOST_NAME}/fullchain.pem"
        privkey_path = f"/etc/letsencrypt/live/{SITE_HOST_NAME}/privkey.pem"
        file_content = f"""# {file_name}

# the upstream component nginx needs to connect to
upstream {project_name} {{
    server unix:{top_dir}/{project_name}.sock;
}}

server {{

    listen 80 default_server;
    listen [::]:80 default_server;
    server_name {SITE_HOST_NAME};

    location / {{
        uwsgi_pass  {project_name};
        include     /etc/nginx/uwsgi_params;
    }}

    return 301 https://$host$request_uri;
}}

server {{
    listen 443 ssl;
    server_name {SITE_HOST_NAME};

    charset     utf-8;

    # max upload size
    client_max_body_size 75M;   # adjust to taste

    location {MEDIA_URL_clean}  {{
        alias {MEDIA_ROOT};
    }}

    location {STATIC_URL_clean} {{
        alias {STATIC_ROOT};
    }}

    location / {{
        uwsgi_pass  {project_name};
        include     /etc/nginx/uwsgi_params;
    }}

    location /geoserver {{
        proxy_pass http://localhost:8080/geoserver;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_redirect off;
    }}

    ssl_certificate {fullchain_path};
    ssl_certificate_key {privkey_path};
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;
}}
"""

        outfile_path = os.path.join(self.out_dir, file_name)

        return self.write_file(outfile_path, file_content)

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

        client = boto3.client("s3", **settings.S3_CONFIG)

        response = client.list_buckets()
        if settings.S3_BUCKET_NAME not in [i["Name"] for i in response["Buckets"]]:
            print(f"Creating bucket: {settings.S3_BUCKET_NAME}")
            client.create_bucket(Bucket=settings.S3_BUCKET_NAME)
            print("Bucket created.")
        else:
            print(f"Bucket already exists: {settings.S3_BUCKET_NAME}")

    def get_plugins(self):
        dest = Path("ohmg/frontend/static/plugins")
        dest.mkdir(exist_ok=True)

        for url in settings.PLUGIN_ASSETS:
            response = requests.get(url)
            print(url)
            with open(Path(dest, url.split("/")[-1]), mode="wb") as file:
                file.write(response.content)

    def create_services(self):
        self.out_dir = ".services"
        celery_service_path = self._write_file(self.generate_celery_service(), "celery.service")
        print(celery_service_path.absolute())

        uwsgi_ini_path = self._write_file(self.generate_uwsgi_ini(), "uwsgi.ini")
        uwsgi_service_path = self._write_file(
            self.generate_uwsgi_service(uwsgi_ini_path), "uwsgi.service"
        )

        print(f"""services created. to deploy, run the following commands:

# update celery 
sudo ln -sf {celery_service_path.absolute()} /etc/systemd/system
sudo systemctl daemon-reload
sudo systemctl restart celery

# update uwsgi
sudo ln -sf {uwsgi_service_path.absolute()} /etc/systemd/system
sudo systemctl daemon-reload
sudo systemctl restart uwsgi
""")
