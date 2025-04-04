class gbemuException(Exception):
    """
    Base class for any Knbn exception
    """


class FetchError(gbemuException):
    pass


class DecodeError(gbemuException):
    pass


class ExecuteError(gbemuException):
    pass


class RomError(gbemuException):
    pass


class CartReadError(gbemuException):
    pass

class CartWriteError(gbemuException):
    pass
