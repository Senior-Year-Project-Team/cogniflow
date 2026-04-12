from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from ppst.models import Clinician, TestSession


class Command(BaseCommand):
    help = "Delete all test sessions for a specific clinician."

    def add_arguments(self, parser):
        parser.add_argument(
            "--clinician",
            type=str,
            required=True,
            help="Clinician id or username/email whose sessions should be deleted.",
        )
        parser.add_argument(
            "--yes",
            action="store_true",
            help="Confirm deletion without an interactive prompt.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        clinician = self._resolve_clinician(options["clinician"])
        session_qs = TestSession.objects.filter(clinician=clinician)
        session_count = session_qs.count()

        if session_count == 0:
            self.stdout.write(
                self.style.WARNING(
                    f"No sessions found for {clinician.user.username}."
                )
            )
            return

        if not options["yes"]:
            raise CommandError(
                "This command deletes all sessions for the selected clinician. "
                "Re-run with --yes to confirm."
            )

        deleted_count, _ = session_qs.delete()
        self.stdout.write(
            self.style.SUCCESS(
                f"Deleted {session_count} session(s) for {clinician.user.username}."
            )
        )

    def _resolve_clinician(self, clinician_value):
        if clinician_value.isdigit():
            clinician = Clinician.objects.filter(id=int(clinician_value)).first()
        else:
            clinician = Clinician.objects.filter(user__username=clinician_value).first()

        if clinician is None:
            raise CommandError(
                f'No clinician found for "{clinician_value}". Use a clinician id or username/email.'
            )

        return clinician
