class NothingToDo(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)
        self.exit_code = 4000
