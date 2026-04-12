import random
import string
from datetime import timedelta

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from ppst.models import Clinician, TestSession, TrialResponse


SCORED_TEST_TRIALS = [
    {"sequence": ["3", "9", "1", "7"], "type": "digit"},
    {"sequence": ["6", "2", "8", "4"], "type": "digit"},
    {"sequence": ["5", "1", "9", "3"], "type": "digit"},
    {"sequence": ["7", "2", "5", "9", "1"], "type": "digit"},
    {"sequence": ["4", "8", "1", "6", "3"], "type": "digit"},
    {"sequence": ["9", "3", "6", "2", "8"], "type": "digit"},
    {"sequence": ["5", "R", "2", "B"], "type": "mixed"},
    {"sequence": ["T", "7", "D", "4"], "type": "mixed"},
    {"sequence": ["8", "N", "1", "K"], "type": "mixed"},
    {"sequence": ["T", "7", "D", "4", "N"], "type": "mixed"},
    {"sequence": ["9", "L", "3", "F", "6"], "type": "mixed"},
    {"sequence": ["M", "2", "S", "8", "C"], "type": "mixed"},
]


class Command(BaseCommand):
    help = "Generate fake patient sessions and trial responses for local development."

    def add_arguments(self, parser):
        parser.add_argument(
            "count",
            type=int,
            default=10,
            nargs="?",
            help="Number of fake patient test sessions to generate.",
        )
        parser.add_argument(
            "--clinician",
            type=str,
            help="Clinician id or username/email to attach the fake sessions to.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        # Wrap the whole run in one transaction so partial fake datasets are not left behind.
        count = options["count"]
        if count < 1:
            self.stderr.write("Count must be at least 1.")
            return

        # Reuse the first clinician if one exists unless a specific one was requested.
        clinician = self._resolve_clinician(options.get("clinician"))
        pending_count = random.randint(0, max(1, count // 3))
        completed_count = count - pending_count
        created = self._create_sessions(
            clinician=clinician,
            completed_count=completed_count,
            pending_count=pending_count,
        )

        clinician_label = (
            clinician.user.username if clinician else "no clinician"
        )
        self.stdout.write(
            self.style.SUCCESS(
                f"Created {created} fake patient test session(s) for {clinician_label} "
                f"({completed_count} completed, {pending_count} pending)."
            )
        )

    def _resolve_clinician(self, clinician_value):
        if not clinician_value:
            return Clinician.objects.order_by("id").first()

        clinician = None
        if clinician_value.isdigit():
            clinician = Clinician.objects.filter(id=int(clinician_value)).first()
        else:
            clinician = Clinician.objects.filter(user__username=clinician_value).first()

        if clinician is None:
            raise CommandError(
                f'No clinician found for "{clinician_value}". Use a clinician id or username/email.'
            )

        return clinician

    def _create_sessions(self, clinician, completed_count, pending_count):
        created_count = 0

        for _ in range(completed_count):
            # Completed sessions include scored trial responses.
            session = TestSession.objects.create(
                clinician=clinician,
                age_bracket=random.choice([choice[0] for choice in TestSession.AGE_BRACKET_CHOICES]),
                language=random.choice([choice[0] for choice in TestSession.LANGUAGE_CHOICES]),
                voice=random.choice([choice[0] for choice in TestSession.VOICE_CHOICES]),
                is_completed=True,
            )

            # Backdate sessions so reports and dashboards look more realistic.
            created_at = timezone.now() - timedelta(
                days=random.randint(1, 60),
                hours=random.randint(0, 23),
                minutes=random.randint(0, 59),
            )
            session.created_at = created_at
            session.completed_at = created_at + timedelta(minutes=random.randint(8, 25))
            self._create_trial_responses(session)
            session.save(update_fields=["created_at", "completed_at"])
            created_count += 1

        for _ in range(pending_count):
            # Pending sessions are recent uncompleted links that should appear on the dashboard.
            session = TestSession.objects.create(
                clinician=clinician,
                age_bracket=random.choice([choice[0] for choice in TestSession.AGE_BRACKET_CHOICES]),
                language=random.choice([choice[0] for choice in TestSession.LANGUAGE_CHOICES]),
                voice=random.choice([choice[0] for choice in TestSession.VOICE_CHOICES]),
                is_completed=False,
            )

            session.created_at = timezone.now() - timedelta(
                hours=random.randint(0, 47),
                minutes=random.randint(0, 59),
            )
            session.save(update_fields=["created_at"])
            created_count += 1

        return created_count

    def _create_trial_responses(self, session):
        # Use the same scored trial structure as the real test interface.
        for trial_number, trial in enumerate(SCORED_TEST_TRIALS, start=1):
            stimulus = list(trial["sequence"])
            trial_type = trial["type"]
            is_correct = random.random() < self._accuracy_for_bracket(session.age_bracket)
            # Wrong answers are generated by slightly mutating the original sequence.
            response = list(stimulus) if is_correct else self._mutate_response(stimulus, trial_type)

            latencies = [random.randint(450, 1600) for _ in response]
            TrialResponse.objects.create(
                session=session,
                trial_number=trial_number,
                trial_type=trial_type,
                stimulus_sequence=",".join(stimulus),
                patient_response=",".join(response),
                latency_ms=sum(latencies),
                latencies_ms=",".join(str(value) for value in latencies),
                is_correct=(response == stimulus),
            )

    def _mutate_response(self, stimulus, trial_type):
        response = list(stimulus)
        if len(response) <= 1:
            return response

        # Introduce a plausible-looking error instead of generating a totally random response.
        mutation = random.choice(["swap", "replace"])
        if mutation == "swap":
            index = random.randint(0, len(response) - 2)
            response[index], response[index + 1] = response[index + 1], response[index]
            return response

        replace_index = random.randrange(len(response))
        if trial_type == "digit" or replace_index % 2 == 0:
            replacement_pool = list(string.digits)
        else:
            replacement_pool = list("ABCDEFGHJKLMNPQRSTUVWXYZ")

        replacement = random.choice(replacement_pool)
        while replacement == response[replace_index]:
            replacement = random.choice(replacement_pool)
        response[replace_index] = replacement
        return response

    def _accuracy_for_bracket(self, age_bracket):
        # Older brackets get slightly lower average accuracy so aggregate stats vary more naturally.
        return {
            "18-24": 0.90,
            "25-34": 0.88,
            "35-44": 0.84,
            "45-54": 0.80,
            "55-64": 0.74,
            "65-74": 0.68,
            "75-84": 0.60,
            "85+": 0.50,
        }.get(age_bracket, 0.75)
