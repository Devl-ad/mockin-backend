# your_app/management/commands/update_earnings.py

from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from users.models import Investments


class Command(BaseCommand):
    help = "Update earnings for investments"

    def handle(self, *args, **kwargs):
        now = timezone.now()
        one_hour_ago = now - timedelta(hours=1)
        investments = Investments.objects.filter(
            status="active", date__lte=one_hour_ago
        )

        for investment in investments:
            # Only process if hours_credited is more than 0
            if investment.hours_credited > 0:
                daily_earn = (
                    investment.package.getHourlyroi() / 100
                ) * investment.amount_invested

                # Add earnings
                investment.amount_earn += daily_earn

                # Decrement hours_credited
                investment.hours_credited -= 1

                # Check if investment should be completed
                if investment.hours_credited == 0:
                    investment.status = "completed"
                    investment.user.balance += (
                        investment.amount_earn + investment.amount_invested
                    )
                    investment.user.save()

                investment.save()

        self.stdout.write(
            self.style.SUCCESS("Successfully updated earnings for investments")
        )
