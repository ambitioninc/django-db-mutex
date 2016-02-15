from django.db import models


class DBMutex(models.Model):
    """
    Models a mutex lock with a ``lock_id`` and a ``creation_time``.

    :type lock_id: str
    :param lock_id: A unique CharField with a max length of 256

    :type creation_time: datetime
    :param creation_time: The creation time of the mutex lock
    """
    lock_id = models.CharField(max_length=256, unique=True)
    creation_time = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'db_mutex'
