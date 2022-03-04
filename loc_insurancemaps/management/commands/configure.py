import os
import sys
import subprocess
from django.conf import settings
from django.core import management
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = 'generate various system configuration files that incorporate the '\
           'the current app settings.'
    out_dir = "_system-configs"
    verbose = False

    def add_arguments(self, parser):
        parser.add_argument(
            "type",
            choices=[
                "supervisor",
                "celery",
                "uwsgi",
                "nginx",
                "nginx-ssl",
                "all",
            ],
            nargs="+",
            help="Choose what configurations to generate."
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

    def handle(self, *args, **options):

        self.verbose = options["verbose"]
        create_all = "all" in options["type"]

        if options["directory"] is not None:
            self.out_dir = os.path.abspath(options['directory'])

        if not os.path.isdir(self.out_dir):
            os.mkdir(self.out_dir)

        outputs = []
        if create_all or "supervisor" in options['type']:
            if self.verbose:
                print("creating supervisord service")
            s_file = self.write_supervisor_config()
            outputs.append(s_file)

            ds_file = self.write_supervisor_deploy(s_file)
            outputs.append(ds_file)

        if create_all or "celery" in options['type']:
            if self.verbose:
                print("creating celery config")
            c_file = self.write_project_celery_config()
            outputs.append(c_file)

            dc_file = self.write_celery_deploy(c_file)
            outputs.append(dc_file)

        if create_all or "uwsgi" in options['type']:
            if self.verbose:
                print("creating uwsgi ini and service configs")
            ini_file = self.write_project_uwsgi_ini()
            outputs.append(ini_file)

            us_file = self.write_uwsgi_service(ini_file)
            outputs.append(us_file)

            du_file = self.write_uwsgi_service_deploy(us_file)
            outputs.append(du_file)

        if create_all or "nginx" in options['type']:
            if self.verbose:
                print("creating nginx site config")
            nginx_site_file = self.write_nginx_site_conf()
            outputs.append(nginx_site_file)

        if create_all or "nginx-ssl" in options['type']:
            if self.verbose:
                print("creating nginx SSL site config")
            nginx_ssl_site_file = self.write_nginx_ssl_site_conf()
            outputs.append(nginx_ssl_site_file)

        if self.verbose:
            print(f"~~~\noutput directory: {os.path.abspath(self.out_dir)}")
            print(f"~~~\nfile count: {len(outputs)}")
            for f in outputs:
                print(os.path.basename(f))

    def resolve_var(self, name, default_value=None):

        value = getattr(settings, name, "<not in django settings>")
        if value == "<not in django settings>":
            value = os.getenv(name, default_value)

        return value

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
            ("CACHE_BUSTING_STATIC_ENABLED", False),
            ("CACHE_BUSTING_MEDIA_ENABLED", False),
            ("SITEURL", ""),
            ("DJANGO_SETTINGS_MODULE", None),
            ("GEOSERVER_ADMIN_PASSWORD", ""),
            ("GEOSERVER_LOCATION", ""),
            ("GEOSERVER_PUBLIC_LOCATION", ""),
            ("GEOSERVER_WEB_UI_LOCATION", ""),
            ("MONITORING_ENABLED", False),
            ("BROKER_URL", ""),
            ("ASYNC_SIGNALS", False),
            ("DATABASE_URL", ""),
            ("GEODATABASE_URL", ""),
            ("CACHE_DIR", ""),
            ("MEDIA_ROOT", ""),
        ]

        if self.resolve_var("EMAIL_ENABLE", False) is True:
            vars += [
                ('EMAIL_ENABLE', True),
                ('DJANGO_EMAIL_BACKEND', 'django.core.mail.backends.smtp.EmailBackend'),
                ('DJANGO_EMAIL_HOST', 'localhost'),
                ('DJANGO_EMAIL_PORT', 587),
                ('DJANGO_EMAIL_HOST_USER', ''),
                ('DJANGO_EMAIL_HOST_PASSWORD', ''),
                ('DJANGO_EMAIL_USE_TLS', False),
                ('DJANGO_EMAIL_USE_SSL', False),
                ('DEFAULT_FROM_EMAIL', 'admin@localhost'),
            ]

        if self.resolve_var("ACCOUNT_OPEN_SIGNUP", False) is True:
            vars += [
                ('ACCOUNT_OPEN_SIGNUP', True),
                ('ACCOUNT_EMAIL_REQUIRED', True),
                ('ACCOUNT_CONFIRM_EMAIL_ON_GET', False),
                ('ACCOUNT_EMAIL_VERIFICATION', True),
                ('ACCOUNT_EMAIL_CONFIRMATION_EMAIL', True),
                ('ACCOUNT_EMAIL_CONFIRMATION_REQUIRED', True),
                ('ACCOUNT_AUTHENTICATION_METHOD', 'username_email'),
                ('AUTO_ASSIGN_REGISTERED_MEMBERS_TO_REGISTERED_MEMBERS_GROUP_NAME', True),
            ]

        kv_list = []
        for var in vars:
            value = self.resolve_var(var[0], var[1])
            kv_list.append(f"{var[0]}=\"{value}\"")
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
sudo pkill celery
sudo supervisorctl reload
"""
        full_deploy_path = self.write_file(deploy_path, deploy_content)

        return full_deploy_path

    def write_project_celery_config(self):

        LOCAL_ROOT = self.resolve_var("LOCAL_ROOT", None)
        project_name = os.path.basename(LOCAL_ROOT)
        top_dir = os.path.dirname(LOCAL_ROOT)
        env_file = os.path.join(top_dir, ".env")
        user = self.resolve_var("USER", "username")
        celery_path = os.path.join(os.path.dirname(sys.executable), "celery")

        file_content = f"""[program:{project_name}-celery]
command=sh -c \'. {env_file} && {celery_path} -A {project_name}.celeryapp:app worker -B -E --loglevel=DEBUG --concurrency=10 -n worker1@%%h'
directory={top_dir}
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
        deploy_content = f"""#!/bin/bash
sudo ln -sf {celery_conf} /etc/supervisor/conf.d/{os.path.basename(celery_conf)}

# Restart supervisor
sudo supervisorctl reload

sudo pkill -f celery
"""
        full_deploy_path = self.write_file(deploy_path, deploy_content)

        return full_deploy_path

    def write_project_uwsgi_ini(self):

        LOCAL_ROOT = self.resolve_var("LOCAL_ROOT")
        wsgi_file = os.path.join(LOCAL_ROOT, "wsgi.py")
        project_name = os.path.basename(LOCAL_ROOT)
        wsgi_application = f"{project_name}.wsgi:application"
        top_dir = os.path.dirname(LOCAL_ROOT)
        env_path = os.path.dirname(os.path.dirname(sys.executable))
        log_dir = self.resolve_var("LOG_DIR", os.path.join(LOCAL_ROOT, "logs"))
        user = self.resolve_var("USER", "username")

        vars = [
            ("MEDIA_ROOT", ""),
            ("DATABASE_URL", ""),
            ("GEODATABASE_URL", ""),
            ("DEBUG", False),
            ("DJANGO_SETTINGS_MODULE", None),
            ("SITE_HOST_NAME", ""),
            ("SITEURL", ""),
            ("ALLOWED_HOSTS", []),
            ("LOCKDOWN_GEONODE", False),
            ("SESSION_EXPIRED_CONTROL_ENABLED", True),
            ("MONITORING_ENABLED", False),
            ("ADMIN_USERNAME", ""),
            ("ADMIN_PASSWORD", ""),
            ("ADMIN_EMAIL", ""),
            ("GEOSERVER_PUBLIC_HOST", "localhost"),
            ("GEOSERVER_PUBLIC_PORT", ""),
            ("GEOSERVER_ADMIN_PASSWORD", ""),
            ("GEOSERVER_LOCATION", ""),
            ("GEOSERVER_PUBLIC_LOCATION", ""),
            ("GEOSERVER_WEB_UI_LOCATION", ""),
            ("OGC_REQUEST_TIMEOUT", 60),
            ("OGC_REQUEST_MAX_RETRIES", 3),
            ("OGC_REQUEST_POOL_MAXSIZE", 100),
            ("OGC_REQUEST_POOL_CONNECTIONS", 100),
            ("MAPBOX_API_TOKEN", None),
            ("MAPSERVER_ENDPOINT", ""),
            ("MONITORING_ENABLED", False),
            ("BROKER_URL", ""),
            ("ASYNC_SIGNALS", False),
            ("THEME_ACCOUNT_CONTACT_EMAIL", "admin@example.com"),
        ]

        if self.resolve_var("EMAIL_ENABLE", False) is True:
            vars += [
                ('EMAIL_ENABLE', True),
                ('DJANGO_EMAIL_BACKEND', 'django.core.mail.backends.smtp.EmailBackend'),
                ('DJANGO_EMAIL_HOST', 'localhost'),
                ('DJANGO_EMAIL_PORT', 587),
                ('DJANGO_EMAIL_HOST_USER', ''),
                ('DJANGO_EMAIL_HOST_PASSWORD', ''),
                ('DJANGO_EMAIL_USE_TLS', False),
                ('DJANGO_EMAIL_USE_SSL', False),
                ('DEFAULT_FROM_EMAIL', 'admin@localhost'),
            ]

        if self.resolve_var("ACCOUNT_OPEN_SIGNUP", False) is True:
            vars += [
                ('ACCOUNT_OPEN_SIGNUP', True),
                ('ACCOUNT_EMAIL_REQUIRED', True),
                ('ACCOUNT_CONFIRM_EMAIL_ON_GET', False),
                ('ACCOUNT_EMAIL_VERIFICATION', True),
                ('ACCOUNT_EMAIL_CONFIRMATION_EMAIL', True),
                ('ACCOUNT_EMAIL_CONFIRMATION_REQUIRED', True),
                ('ACCOUNT_AUTHENTICATION_METHOD', 'username_email'),
                ('AUTO_ASSIGN_REGISTERED_MEMBERS_TO_REGISTERED_MEMBERS_GROUP_NAME', True),
            ]

        env_section = ""
        for var in vars:
            value = self.resolve_var(var[0], var[1])
            env_section += f"env = {var[0]}={value}\n"

        # this one must be quoted because it could contain # (comment tag)
        secret = self.resolve_var("SECRET_KEY", "RanD0m%3cr3tK3y")
        env_section += f"env = SECRET_KEY=\"{secret}\""

        file_content = f"""[uwsgi]
# set socket and set its permissions
socket = {top_dir}/{project_name}.sock
chmod-socket = 664

# set user and group for process
uid = {user}
gid = www-data

# set log paths and daemon mode
logto = {log_dir}/uwsgi.log

pidfile = /tmp/{project_name}.pid

# set location of wsgi app
chdir = {top_dir}
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

        outfile_path = os.path.join(self.out_dir, "uwsgi.ini")

        return self.write_file(outfile_path, file_content)

    def write_uwsgi_service(self, ini_file="<UPDATE WITH PATH TO .ini FILE>"):

        uwsgi_path = os.path.join(os.path.dirname(sys.executable), "uwsgi")
        user = self.resolve_var("USER", "username")
        LOCAL_ROOT = self.resolve_var("LOCAL_ROOT")
        project_name = os.path.basename(LOCAL_ROOT)

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

    def write_uwsgi_service_deploy(self, service_file):

        deploy_path = os.path.join(self.out_dir, "deploy-uwsgi-service.sh")
        service_name = os.path.splitext(os.path.basename(service_file))[0]
        deploy_content = f"""#!/bin/bash
sudo ln -sf {service_file} /etc/systemd/system

# refresh service
sudo systemctl daemon-reload
sudo pkill uwsgi
sudo systemctl stop {service_name}
sudo systemctl start {service_name}
"""
        full_deploy_path = self.write_file(deploy_path, deploy_content)

        return full_deploy_path

    def write_nginx_site_conf(self):

        SITE_HOST_NAME = self.resolve_var("SITE_HOST_NAME")
        file_name = SITE_HOST_NAME + ".conf"

        MEDIA_ROOT = self.resolve_var("MEDIA_ROOT")
        MEDIA_URL = self.resolve_var("MEDIA_URL")
        MEDIA_URL_clean = MEDIA_URL.rstrip("/")

        STATIC_ROOT = self.resolve_var("STATIC_ROOT")
        STATIC_URL = self.resolve_var("STATIC_URL")
        STATIC_URL_clean = STATIC_URL.rstrip("/")

        LOCAL_ROOT = self.resolve_var("LOCAL_ROOT")
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

        SITE_HOST_NAME = self.resolve_var("SITE_HOST_NAME")
        file_name = SITE_HOST_NAME + "-ssl.conf"

        MEDIA_ROOT = self.resolve_var("MEDIA_ROOT")
        MEDIA_URL = self.resolve_var("MEDIA_URL")
        MEDIA_URL_clean = MEDIA_URL.rstrip("/")

        STATIC_ROOT = self.resolve_var("STATIC_ROOT")
        STATIC_URL = self.resolve_var("STATIC_URL")
        STATIC_URL_clean = STATIC_URL.rstrip("/")

        LOCAL_ROOT = self.resolve_var("LOCAL_ROOT")
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
