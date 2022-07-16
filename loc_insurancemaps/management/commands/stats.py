import os
import csv
from datetime import datetime, timedelta
import logging

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django.db import transaction

from georeference.models import GeorefSession, PrepSession, TrimSession, SessionBase

from loc_insurancemaps.models import get_volume, Volume

logger = logging.getLogger(__name__)

def get_date(date):
    return date - timedelta(hours=6)

def get_date_str(date):
    return get_date(date).strftime("%Y-%m-%d")

def get_week_bins(start_date="2022-01-31"):
    start_week = datetime.strptime(start_date, "%Y-%m-%d")
    end_week = start_week + timedelta(days=6)

    week_bins = {}
    for i in range(1, 19):
        week_bins[i] = {
            "start": start_week,
            "end": end_week,
        }
        start_week = end_week + timedelta(days=1)
        end_week = start_week + timedelta(days=6)
    return week_bins

def get_date_dict(start_date="2022-01-31"):
    dates = {}
    date = datetime.strptime(start_date, "%Y-%m-%d")
    while date < datetime.strptime("2022-06-01", "%Y-%m-%d"):
        dates[date.strftime("%Y-%m-%d")] = {}
        date = date + timedelta(days=1)
    return dates

def get_path(file_name):
    outdir = os.path.join(os.path.dirname(os.path.dirname(settings.LOCAL_ROOT)), "stats")
    if not os.path.isdir(outdir):
        os.mkdir(outdir)
    return os.path.join(outdir, file_name)

def write_dict_csv(file_name, rows):

    if len(rows) > 0:
        print(f"writing file: {file_name}")
        with open(get_path(file_name), "w") as o:
            writer = csv.DictWriter(o, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)
    else:
        print("no rows, no write :(")

## ----------------------------------------------------------------------------

class Command(BaseCommand):
    help = 'generates various csvs used for data analysis.'

    def add_arguments(self, parser):
        parser.add_argument(
            "operation",
            help="the existing username to be changed.",
            choices=[
                "user-signups",
                "sessions-by-user",
                "sessions-by-date",
                "sessions-by-week",
                "session-list",
                "volume-activity",
                "all"
            ]
        )
        parser.add_argument(
            "--exclude-admins",
            action="store_true",
        )

    def handle(self, *args, **options):

        data = []

        admins = get_user_model().objects.filter(username__in=["acfc", "admin"])
        users = get_user_model().objects.all().exclude(username__in=["acfc", "admin", "AnonymousUser"])

        if options['exclude_admins']:
            volumes =  Volume.objects.all().exclude(loaded_by__in=admins)
            sessions = SessionBase.objects.all().exclude(user__in=admins)
        else:
            volumes = Volume.objects.all()
            sessions = SessionBase.objects.all()

        if options['operation'] in ["sessions-by-user", "all"]:

            rows = []
            for user in get_user_model().objects.all():
                rows.append({
                    "email": user.email,
                    "username": user.username,
                    "user_joined": get_date_str(user.date_joined),
                    "volumes": volumes.filter(loaded_by=user).count(),
                    "prep": sessions.filter(type="p").filter(user=user).count(),
                    "georef": sessions.filter(type="g").filter(user=user).count(),
                    "trim": sessions.filter(type="t").filter(user=user).count(),
                    "total": sessions.filter(user=user).count()
                })
            write_dict_csv("sessions-by-user.csv", rows)

        if options['operation'] in ["sessions-by-date", "all"]:

            dates = get_date_dict()
            for v in dates.values():
                v["v"] = 0
                v["p"] = 0
                v["g"] = 0
                v["t"] = 0

            date_list = []
            for s in sessions:
                date_list.append((get_date_str(s.date_created), s.type))
            for v in volumes:
                date_list.append((get_date_str(v.load_date), "v"))
            for item in date_list:
                d, t = item
                if d in dates:
                    dates[d][t] += 1
        
            rows = []
            for k in sorted(dates.keys()):
                v = dates[k]
                rows.append({
                    "date": k,
                    "volumes": dates[k]['v'],
                    "preparation": dates[k]['p'],
                    "georeference": dates[k]['g'],
                    "trim": dates[k]['t'],
                })
            write_dict_csv("sessions-by-date.csv", rows)                

            # if options['operation'] in ["sessions-by-week", "all"]:
            start_week = datetime.strptime("2022-01-31", "%Y-%m-%d")
            end_week = start_week + timedelta(days=6)

            session_bins = get_week_bins()
            # add custom data holders for this set of data
            for v in session_bins.values():
                v["v"] = 0
                v["p"] = 0
                v["g"] = 0
                v["t"] = 0

            for item in date_list:
                d, t = item
                d_date = datetime.strptime(d, "%Y-%m-%d")
                for v in session_bins.values():
                    if d_date >= v['start'] and d_date <= v['end']:
                        v[t] += 1

            rows = []
            for k in sorted(session_bins.keys()):
                v = session_bins[k]
                rows.append({
                    "week_no": k,
                    "start_date": session_bins[k]["start"],
                    "end_date": session_bins[k]["end"],
                    "volumes": session_bins[k]["v"],
                    "preparation": session_bins[k]["p"],
                    "georeference": session_bins[k]["g"],
                    "trim": session_bins[k]["t"],
                })
            write_dict_csv("sessions-by-week.csv", rows)

        if options['operation'] in ["user-signups", "all"]:


            users = get_user_model().objects.all().exclude(username__in=["admin", "acfc", "AnonymousUser"])

            dates = get_date_dict("2022-02-03")
            for v in dates.values():
                v["new_users"] = 0

            for u in users:
                cleaned_join_date = datetime.strptime(u.date_joined.strftime("%Y-%m-%d"), "%Y-%m-%d")
                join_date = get_date(cleaned_join_date)
                # for those who joined technically before the start, change join date to first day of study
                if join_date < datetime.strptime("2022-02-03", "%Y-%m-%d"):
                    join_date = datetime.strptime("2022-02-03", "%Y-%m-%d")
                join_date_str = get_date_str(join_date)
                if join_date_str in dates:
                    dates[join_date_str]['new_users'] += 1
            
            total = 0
            rows = []
            for k,v in dates.items():
                total += v['new_users']
                v['total'] = total
                rows.append({
                    "date": k,
                    "new_users": v['new_users'],
                    "total_users": v['total']
                })

            write_dict_csv("signups-by-date.csv", rows)

            user_bins = get_week_bins(start_date="2022-02-03")
            for v in user_bins.values():
                v['new_users'] = 0
            for u in users:
                cleaned_join_date = datetime.strptime(get_date_str(u.date_joined), "%Y-%m-%d")
                join_date = get_date(cleaned_join_date)
                # for those who joined technically before the start, change join date to first day of study
                if join_date < user_bins[1]["start"]:
                    join_date = user_bins[1]["start"]
                for v in user_bins.values():
                    if join_date >= v['start'] and join_date <= v['end']:
                        v['new_users'] += 1

            rows = []
            for k in sorted(user_bins.keys()):
                rows.append({
                    "week_no": k,
                    "start_date": user_bins[k]["start"],
                    "end_date": user_bins[k]["end"],
                    "new_users": user_bins[k]["new_users"]
                })
            write_dict_csv("signups-by-week.csv", rows)
                

        if options['operation'] in ["session-list", "all"]:

            sessions = SessionBase.objects.all().order_by("date_created")
            headers = ["create_date", "seconds", "user", "city", "year", "volume"]
            p_headers = headers + ["split", "div_count"]
            g_headers = headers + ["gcp_count"]

            prep_session_rows = []
            georef_session_rows = []
            trim_session_rows = []

            for s in sessions:
                if s.type == "p" or s.type == "g" and s.document is not None:
                    vol = get_volume("document", s.document.pk)
                elif s.type == "t" and s.layer is not None:
                    vol = get_volume("layer", s.layer.pk)
                else:
                    continue
                if vol is None:
                    print(f"can't get volume for resource attached to {s.pk}")
                    continue

                row = {i: "" for i in headers}
                row["create_date"] = get_date_str(s.date_created)
                row["seconds"] = 0
                if s.date_run and s.date_created:
                    diff = s.date_run - s.date_created
                    row["seconds"] = diff.total_seconds()
                row["user"] = s.user.username
                row["city"] = vol.city
                row["year"] = vol.year
                row["volume"] = vol.__str__()
                row["volume_id"] = vol.pk

                if s.type == "p":
                    row["split"] = s.data['split_needed']
                    row["div_count"] = len(s.data['divisions'])
                    prep_session_rows.append(row)

                if s.type == "g":
                    row["gcp_count"] = len(s.data['gcps']['features'])
                    georef_session_rows.append(row)

                if s.type == "t":
                    trim_session_rows.append(row)

            print(len(prep_session_rows), "prep sessions to write")
            print(len(georef_session_rows), "georef sessions to write")
            print(len(trim_session_rows), "trim sessions to write")

            write_dict_csv("sessions-prep.csv", prep_session_rows)
            write_dict_csv("sessions-georef.csv", georef_session_rows)
            write_dict_csv("sessions-trim.csv", trim_session_rows)

        if options['operation'] in ["volume-activity", "all"]:

            # volume participation
            rows = []
            for v in Volume.objects.all():
                print(v)
                dps = v.get_all_documents()
                documents = [i.resource for i in dps]
                layers = [i.get_layer() for i in dps if not i.get_layer() is None]
                s1 = SessionBase.objects.filter(document__in=documents)
                s2 = SessionBase.objects.filter(layer__in=layers)
                s = s1 | s2
                s_noadmins = s.exclude(user__in=admins)
                usernames = set([i.user.username for i in s])
                usernames_noadmins = set([i.user.username for i in s_noadmins])
                rows.append({
                    "id": v.pk,
                    "volume": str(v),
                    "city": v.city,
                    "year": v.year,
                    "load_date": v.load_date.strftime("%Y-%m-%d"),
                    "load_username": v.loaded_by.username,
                    "prep_ct": s.filter(type="p").count(),
                    "georef_ct": s.filter(type="g").count(),
                    "trim_ct": s.filter(type="t").count(),
                    "total_sessions": s.count(),
                    "user_ct": len(usernames),
                    "usernames": ",".join(usernames),
                    "load_user_participated": v.loaded_by.username in usernames,
                    "prep_ct_noadmins": s_noadmins.filter(type="p").count(),
                    "georef_ct_noadmins": s_noadmins.filter(type="g").count(),
                    "trim_ct_noadmins": s_noadmins.filter(type="t").count(),
                    "total_sessions_noadmins": s_noadmins.count(),
                    "user_ct_noadmins": len(usernames_noadmins),
                    "usernames_noadmins": ",".join(usernames_noadmins),
                })

            write_dict_csv("volume-activity.csv", rows)
