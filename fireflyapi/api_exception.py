class APIException(Exception):
    """
    Basic Exception type raised on API "errors"
    """
    def __init__(self, msg):
        super(APIException, self).__init__(msg)
