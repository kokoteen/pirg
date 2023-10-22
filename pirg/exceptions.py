class DisabledPipFlag(Exception):
    def __init__(self, message: str):
        self.message = message
        self.exit_code = 4001
        super().__init__(self.message)


class WrongPkgName(Exception):
    def __init__(self, message: str):
        self.message = message
        self.exit_code = 4002
        super().__init__(self.message)


class WrongSpecifierSet(Exception):
    def __init__(self, message: str):
        self.message = message
        self.exit_code = 4003
        super().__init__(self.message)


class EmptyDatabase(Exception):
    def __init__(self, message: str):
        self.message = message
        self.exit_code = 4004
        super().__init__(self.message)
