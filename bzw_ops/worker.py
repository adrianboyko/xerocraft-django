# See https://devcenter.heroku.com/articles/python-rq

# Standard
import os

# Third Party
import redis
from rq import Worker, Queue, Connection
import django

django.setup()

listen = ['high', 'default', 'low']

redis_url = os.getenv('REDISTOGO_URL', 'redis://localhost:6379')

conn = redis.from_url(redis_url)

if __name__ == '__main__':

    # Was seeing errors such as the following:
    #    return self.create_cursor()
    #    File "[...]/django/db/backends/postgresql/base.py", line 210, in create_cursor
    #    cursor = self.connection.cursor()
    #    django.db.utils.InterfaceError: connection already closed
    #
    # Discussions online suggest that this may be related to problems in Django/Redis systems
    # and suggested resetting the database connection by calling close_connection. The method
    # was removed in Django 1.8 but https://github.com/arteria/django-compat/issues/39
    # indicated that close_old_connections is equivalent.
    #
    # Was able to reproduce the issue locally and close_old_connections() does seem to fix the problem.
    django.db.close_old_connections()

    with Connection(conn):
        worker = Worker(map(Queue, listen))
        worker.work()
