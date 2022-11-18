


class ResponseError(Exception):
    message = 'Unexpected response. '

    def __str__(self) -> str:
        return self.message + f'Details: {self.args}'

class ResponseSchemaError(ResponseError):
    message = 'Unexpected response data schema. '