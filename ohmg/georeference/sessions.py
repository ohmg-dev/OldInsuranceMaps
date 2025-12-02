import logging
from typing import TYPE_CHECKING, Union

from django.contrib.contenttypes.models import ContentType
from django.utils import timezone

if TYPE_CHECKING:
    from ohmg.core.models import Document, Layer, Region

    from .models import GeorefSession, PrepSession

logger = logging.getLogger(__name__)


def add_lock(
    session: Union["PrepSession", "GeorefSession"], obj: Union["Document", "Region", "Layer"]
):
    from .models import SessionLock

    ct = ContentType.objects.get_for_model(obj)
    SessionLock.objects.create(
        session=session,
        target_type=ct,
        target_id=obj.pk,
        user=session.user,
    )


def remove_lock(
    session: Union["PrepSession", "GeorefSession"], obj: Union["Document", "Region", "Layer"]
):
    ct = ContentType.objects.get_for_model(obj)
    session.locks.filter(target_type=ct, target_id=obj.pk).delete()


def delete_expired_session_locks():
    """Look at all current SessionLocks, and if one is expired and it's session is
    still on the "input" stage, then delete the session (the lock will be deleted as well)
    """
    from .models import SessionBase, SessionLock

    locks = SessionLock.objects.all()
    if locks.count() > 0:
        sessions = set([i.session for i in locks])
        logger.info(f"{locks.count()} SessionLock(s) currently exist from {len(sessions)} sessions")
    now = timezone.now().timestamp()
    stale = set()
    for lock in locks:
        if now > lock.expiration.timestamp() and lock.session.stage == "input":
            stale.add(lock.session.pk)

    if stale:
        logger.info(f"deleting {len(stale)} stale session(s): {','.join([str(i) for i in stale])}")
        SessionBase.objects.filter(pk__in=stale).delete()
