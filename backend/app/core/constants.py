from datetime import timedelta
from decimal import Decimal

# Initial loan length (due_at = borrowed_at + this many days).
LOAN_DEFAULT_DAYS = 14
# Single renewal adds this many days to the current due_at (not another full loan period).
RENEWAL_EXTRA_DAYS = 4
FINE_PER_OVERDUE_DAY = Decimal("2.00")
MAX_ACTIVE_LOANS_PER_USER = 3
MAX_PENDING_RESERVATIONS_PER_USER = 3
# When return frees a copy but the head of the queue already has max loans: hold with this TTL.
# Produção (1 hora) — descomente em produção e ajuste reservation_hold_timedelta() para usar horas.
# RESERVATION_HOLD_HOURS = 1

# Desenvolvimento / testes: janela curta até hold_until (expiração via Celery task expire_reservation_holds).
RESERVATION_HOLD_MINUTES = 3


def reservation_hold_timedelta() -> timedelta:
    """TTL da janela de hold após devolução quando o usuário está no limite de empréstimos."""
    # Produção:
    # return timedelta(hours=RESERVATION_HOLD_HOURS)
    return timedelta(minutes=RESERVATION_HOLD_MINUTES)


# Copy estável para o corpo da notificação (produto). Em dev o TTL real pode ser menor — ver README/decisões.
RESERVATION_HOLD_NOTIFICATION_DEADLINE_COPY = "1 hora(s)"

# Patron may request renewal only during the first N calendar days on loan (day N+1 onward: denied).
RENEWAL_REQUEST_CALENDAR_DAY_LIMIT = 7
# One renewal per loan; only if not overdue, within request window, and no waitlist for the copy.
MAX_LOAN_RENEWALS = 1
