import os
import sys
from django.conf import settings
from django.core import management
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = 'generate various system configuration files that incorporate the '\
           'the current app settings.'
    out_dir = "_system-configs"

    def add_arguments(self, parser):
        parser.add_argument(
            "type",
            choices=["supervisor", "celery", "uwsgi", "nginx"],
            nargs="+",
            help="Choose what configurations to generate."
        )
        parser.add_argument(
            "-d",
            "--directory",
            help="Directory where the generated files will be placed.",
        )
        parser.add_argument(
            "--deploy",
            action="store_true",
            help="Attempts to deploy the new settings to system locations.",
        )

    def handle(self, *args, **options):

        if options["directory"] is not None:
            self.out_dir = os.path.abspath(options['directory'])

        if not os.path.isdir(self.out_dir):
            os.mkdir(self.out_dir)

        if "supervisor" in options['type']:
            s_file = self.write_supervisor_config()

        if "celery" in options['type']:
            c_file = self.write_project_celery_config()

        if "uwsgi" in options['type']:
            ini_file = self.write_project_uwsgi_ini()
            us_file = self.write_uwsgi_service(ini_file)

        if "nginx" in options['type']:
            nginx_site_file = self.write_nginx_site_conf()

    def resolve_var(self, name, default_value=None):

        value = getattr(settings, name, "<not in django settings>")
        if value == "<not in django settings>":
            value = os.getenv(name, default_value)

        return value

    def write_file(self, file_path, content):

        with open(file_path, "w") as out:
            out.write(content)
        return file_path

    def write_supervisor_config(self):

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
        ]

        var_str = ""
        for var in vars:
            value = self.resolve_var(var[0], var[1])
            var_str += f"{var[0]}=\"{value}\","
        var_str_clean = var_str.rstrip(",")

        file_content = f"""; supervisor config file

[unix_http_server]
file=/var/run/supervisor.sock   ; (the path to the socket file)
chmod=0700                       ; sockef file mode (default 0700)

[supervisord]
nodaemon=true
logfile=/var/log/supervisor/supervisord.log ; (main log file;default $CWD/supervisord.log)
pidfile=/var/run/supervisord.pid ; (supervisord pidfile;default supervisord.pid)
childlogdir=/var/log/supervisor            ; ('AUTO' child log dir, default $TEMP)
environment={var_str_clean}

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

        return self.write_file(outfile_path, file_content)

    def write_project_celery_config(self):

        LOCAL_ROOT = self.resolve_var("LOCAL_ROOT", None)
        project_name = os.path.basename(LOCAL_ROOT)
        top_dir = os.path.dirname(LOCAL_ROOT)
        user = self.resolve_var("USER", "username")
        celery_path = os.path.join(os.path.dirname(sys.executable), "celery")

        file_content = f"""[program:{project_name}-celery]
command=sh -c \'{celery_path} -A {project_name}.celeryapp:app worker -B -E --loglevel=DEBUG --concurrency=5 -n worker1@%%h'
directory={top_dir}
user={user}
numproc=1
stdout_logfile=/var/log/{project_name}-celery.log
stderr_logfile=/var/log/{project_name}-celery.log
autostart=true
autorestart=true
startsecs=10
stopwaitsecs=600
"""

        outfile_path = os.path.join(self.out_dir, f"{project_name}-celery.conf")

        return self.write_file(outfile_path, file_content)

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
            ("SECRET_KEY", "RanD0m%3cr3tK3y"),
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
            ("OGC_REQUEST_POOL_CONNECTIONS", 100)
        ]

        env_section = ""
        for var in vars:
            value = self.resolve_var(var[0], var[1])
            env_section += f"env = {var[0]}={value}\n"

        file_content = f"""[uwsgi]
# set socket and set its permissions
socket = {top_dir}/{project_name}.sock
chmod-socket = 664

# set user and group for process
uid = {user}
gid = www-data

# set log paths and daemon mode
logto = {log_dir}/uwsgi.log
daemonize = {log_dir}/uwsgi.log

pidfile = /tmp/{project_name}.pid

# set location of wsgi app
chdir = {top_dir}
module = {wsgi_application}

# virtual env location, not sure if both of these are needed
home = {env_path}
virtualenv = {env_path}

{env_section}
# other geonode doc-recommended settings
strict = false
master = true
enable-threads = true
vacuum = true                        ; Delete sockets during shutdown
single-interpreter = true
die-on-term = true                   ; Shutdown when receiving SIGTERM (default is respawn)
need-app = true

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

        outfile_path = os.path.join(self.out_dir, project_name+"_uwsgi.ini")

        return self.write_file(outfile_path, file_content)

    def write_uwsgi_service(self, ini_file="<UPDATE WITH PATH TO .ini FILE>"):

        activate = os.path.join(os.path.dirname(sys.executable), "activate")
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
ExecStart=/bin/bash -c 'source {activate} && uwsgi --ini {ini_file}'
Restart=on-failure
RestartSec=10s

[Install]
WantedBy=multi-user.target
"""

        outfile_path = os.path.join(self.out_dir, project_name+".service")

        return self.write_file(outfile_path, file_content)

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
