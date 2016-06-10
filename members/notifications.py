from members.models import Member, Pushover
import os
import chump
import logging

# TODO: This was created before the "abutils" app. Move it there.

pushover = chump.Application(os.environ['PUSHOVER_API_KEY'])
assert pushover.is_authenticated
logger = logging.getLogger("members")


# REVIEW: This sometimes fails. Should it be an asynchronous task with retries?
def notify(target_member: Member, title: str, message: str):
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
