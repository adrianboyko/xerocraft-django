
# Standard
import os
import logging
from typing import Optional

# Third-party
import pushover
from django.conf import settings

# Local
from members.models import Member, Pushover

TESTING = getattr(settings, 'TESTING', False)

logger = logging.getLogger("members")

pushover_available = False

api_token = os.getenv('XEROPS_PUSHOVER_API_KEY', None)

if api_token is None:
    logger.info("Pushover not configured. Alerts will not be sent.")
else:
    try:
        pushover.init(api_token)
        pushover_available = True
    except Exception as e:
        logger.info("Pushover could not be initialized. Alerts will not be sent.")
        logger.info("Pushover init exception: "+str(e))


# REVIEW: This sometimes fails. Should it be an asynchronous task with retries?
def notify(
  target_member: Member,
  title: str,
  message: str,
  url: str = None,
  url_title: str = None) -> bool:

    if TESTING:
        notify.MOST_RECENT_MEMBER = target_member
        notify.MOST_RECENT_TITLE = title
        notify.MOST_RECENT_MESSSAGE = message
        return True

    if not pushover_available:
        return False

    # TODO: Code currently only uses Pushover mechanism. Should be updated to use alternate mechanisms.
    try:
        target_key = Pushover.objects.get(who=target_member).key
        client = pushover.Client(target_key)
        client.send_message(message, title=title, url=url, url_title=url_title)
        return True
    except Pushover.DoesNotExist:
        logger.warning("Couldn't send msg to %s since there's no pushover key for them.", str(target_member))
        return False
    except Exception as e:
        logger.error("Couldn't send msg to %s because %s", str(target_member), str(e))
        return False

# These were added to support testing:
notify.MOST_RECENT_TITLE = None  # type: Optional[str]
notify.MOST_RECENT_MESSSAGE = None  # type: Optional[str]
notify.MOST_RECENT_MEMBER = None # type: Optional[Member]
