from django.core.management.base import BaseCommand

from ohmg.georeference.models import (
    delete_expired_session_locks,
    SessionBase,
    PrepSession,
    GeorefSession,
)
from ohmg.georeference.operations.sessions import run_preparation, run_georeferencing
from ohmg.loc_insurancemaps.models import find_volume

class Command(BaseCommand):
    help = 'Command line access point for the internal georeferencing utilities.'
    def add_arguments(self, parser):
        parser.add_argument(
            "operation",
            choices=[
                "run",
                "run2",
                "undo",
                "redo",
                "list",
                "delete-expired",
            ],
            help="specify the operation to carry out",
        )
        parser.add_argument(
            "--type",
            choices=[
                "preparation",
                "georeference",
                "trim",
                "all",
            ],
            help="type of session to manage",
        )
        parser.add_argument(
            "--clean",
            action="store_true",
            help="remove all instances of new sessions before migrating legacy ones",
        )
        parser.add_argument(
            "--pk",
            help="primary key for existing session to manage",
        )
        parser.add_argument(
            "--docid",
            help="document id used to find sessions during list operation",
        )

    def _model_from_type(self, session_type):
        if session_type == "p":
            return PrepSession
        elif session_type == "g":
            return GeorefSession

    def handle(self, *args, **options):

        operation = options['operation']
        if operation in ['run', 'run2', 'undo', 'redo']:

            bs = SessionBase.objects.get(pk=options['pk'])
            model = self._model_from_type(bs.type)
            session = model.objects.get(pk=options['pk'])

            if operation == "run":
                session.run()
            if operation == "run2":
                if bs.type == "p":
                    run_preparation(session)
                elif bs.type == "g":
                    run_georeferencing(session)
            elif operation == "redo":
                if bs.type == "p":
                    session.undo(keep_session=True)
                    session.run()
                else:
                    # this is the same as run for georeference sessions
                    # because all previous outputs are reliably overwritten
                    session.run()
            elif operation == "undo":
                vol = find_volume(session.doc)
                session.undo()
                vol.refresh_lookups()


        elif operation == "list":

            if options["type"]:
                model = self._model_from_type(options['type'])
                for s in model.objects.filter(doc2_id=options['docid']):
                    print(s)
            else:
                for ps in PrepSession.objects.filter(doc2_id=options['docid']):
                    print(ps)
                for gs in GeorefSession.objects.filter(doc2_id=options['docid']):
                    print(gs)


        elif operation == 'delete-expired':

            delete_expired_session_locks()
