from django.db import models


class DBMutex(models.Model):
    """
    Models a mutex lock with a lock ID and a creation time.
    """
    lock_id = models.CharField(max_length=256, unique=True)
    creation_time = models.DateTimeField(auto_now_add=True)
