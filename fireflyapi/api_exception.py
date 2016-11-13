class APIException(Exception):
    """
    Basic Exception type raised on API "errors"
    """
    def __init__(self, msg, json=None):
        self.json = json
        super(APIException, self).__init__(msg)
