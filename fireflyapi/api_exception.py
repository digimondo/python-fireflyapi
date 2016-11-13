class APIException(Exception):
    """
    Basic Exception type raised on API "errors"
    """
    def __init__(self, msg, json=None):
        self.json = json
        super(APIException, self).__init__(msg)


class EntityAlreadyCreatedError(APIException):
    """
    Error raised if trying to create an entity that already exists (i.e. doubled device eui)
    """
    def __init__(self, json):
        super(EntityAlreadyCreatedError, self).__init__('entitiy already exists', json)


class EntityNotFoundError(APIException):
    """
    Error raised if trying to access an entity that does exists
    """

    def __init__(self, json):
        super(EntityNotFoundError, self).__init__('entity does not exists', json)