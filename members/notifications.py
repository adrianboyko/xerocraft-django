from members.models import Member, Pushover
import os
import chump
import logging

# TODO: This was created before the "abutils" app. Move it there.

logger = logging.getLogger("members")

key = os.getenv('PUSHOVER_API_KEY', None)
if key is not None:
    pushover = chump.Application(key)
    assert pushover.is_authenticated
else:
    pushover = None
    logger.info("Pushover not configured. Alerts will not be sent.")


# REVIEW: This sometimes fails. Should it be an asynchronous task with retries?
def notify(target_member: Member, title: str, message: str):
    if pushover is None:
        return

    try:
        target_key = Pushover.objects.get(who=target_member).key
    except Pushover.DoesNotExist:
        logger.error("Couldn't send msg to %s since there's no pushover key for them.", str(target_member))
        return

    try:
        pushover_user = pushover.get_user(target_key)
        assert pushover_user.is_authenticated
        message = pushover_user.send_message(message, title=title)
    except Exception as e:
        logger.error("Couldn't send msg to %s because %s", str(target_member), str(e))
