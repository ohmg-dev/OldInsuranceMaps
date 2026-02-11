import os
import subprocess
from datetime import datetime
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    """Run pg_dump to SQL file. Creates a local file and then uploads to S3.
    This command assumes you have the aws cli tool installed and configured.

    Follows this backup pattern:

    - Daily backups for the last 10 days
    - Backups on the 1st and 15th of each month forever

    Daily backups are stored locally and rotated everyday. Directory structure:
    LOCAL
      .db_backups/daily/
        <YYYYMMDD>__<db name>.sql
        (repeated for the last 10 days)

    S3
      bucket_name/daily <- synced from local daily directory
      YYYY/
       all 1st and 15th of the month backups for one year
      YYYY/
       same for another year, etc.
    """

    def __init__(self, *args, **kwargs):
        self.help = self.__doc__

    def add_arguments(self, parser):
        parser.add_argument(
            "bucket-name",
        )
        parser.add_argument(
            "--aws-profile",
            help="Optionally pass a specific aws profile to be used for the upload command",
        )
        parser.add_argument(
            "--skip-sync",
            action="store_true",
            help="Don't sync the daily backups to S3 (useful during testing)",
        )
        parser.add_argument(
            "--skip-rotate",
            action="store_true",
            help="Don't rotate and trim off dailies older than 10 days",
        )

    def handle(self, *args, **options):
        def apply_profile(cmd: list):
            if options["aws_profile"]:
                cmd += ["--profile", options["aws_profile"]]
            return cmd

        bucket = options["bucket-name"]
        now = datetime.now()

        backup_dir = Path(Path(settings.APP_ROOT).parent, ".db_backups", "daily")
        backup_dir.mkdir(exist_ok=True, parents=True)

        db_name = settings.DATABASES["default"]["NAME"]
        db_user = settings.DATABASES["default"]["USER"]
        db_host = settings.DATABASES["default"]["HOST"]
        db_pass = settings.DATABASES["default"]["PASSWORD"]
        db_port = settings.DATABASES["default"]["PORT"]

        fname = now.strftime(f"%Y%m%d__{db_name}.sql")
        fpath = Path(backup_dir, fname)

        cmd = [
            "pg_dump",
            "-U",
            db_user,
            "-h",
            db_host,
            "-p",
            str(db_port),
            "-f",
            str(fpath.resolve()),
            db_name,
        ]

        use_env = os.environ.copy()
        use_env["PGPASSWORD"] = db_pass
        p = subprocess.Popen(cmd, env=use_env)
        exit_code = p.wait()
        print(f"pg_dump exit code: {exit_code}")

        day, year = now.day, now.year

        ## on the 1st and 15th of the month upload the dump to yearly archive
        if day in [1, 15]:
            cmd2 = ["aws", "s3", "cp", fpath, f"s3://{bucket}/{year}/"]
            cmd2 = apply_profile(cmd2)
            subprocess.run(cmd2)

        if not options["skip_rotate"]:
            ## cleanup any local files that are over 10 days old.
            ## sort all of the existing local daily files
            local_dailies = sorted(list(backup_dir.glob("*")))
            limit = 10
            ## slice off any local dailies beyond the limit
            for path in local_dailies[:-limit]:
                os.remove(path)

        if not options["skip_sync"]:
            cmd3 = [
                "aws",
                "s3",
                "sync",
                str(backup_dir.resolve()),
                f"s3://{bucket}/daily/",
                "--delete",
            ]
            cmd3 = apply_profile(cmd3)
            subprocess.run(cmd3)
