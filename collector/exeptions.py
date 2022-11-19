class _BaseExeption(Exception):
    message: str = ''

    def __init__(self, *args: object, msg: str = '') -> None:
        self.message = msg or self.message
        super().__init__(*args)

    def __str__(self) -> str:
        return self.message + f'Details: {self.args}'


class ResponseError(_BaseExeption):
    message = 'Unexpected response. '


class ResponseSchemaError(ResponseError):
    message = 'Unexpected response data schema. '


class NoDataError(_BaseExeption):
    message = 'No data privided.'
