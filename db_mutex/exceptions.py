class DBMutexError(Exception):
    """
    Thrown when a lock cannot be acquired.
    """
    pass


class DBMutexTimeoutError(Exception):
    """
    Thrown when a lock times out before it is released.
    """
    pass
