from my_learn.exception.error_code import ErrorCode


class AgentException(BaseException):
    def __init__(self, error_code: ErrorCode):
        self.code = error_code.code
        self.msg = error_code.msg
        super().__init__(f"{error_code.code}:{error_code.msg}")


