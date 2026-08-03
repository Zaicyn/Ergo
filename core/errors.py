class MCLError(Exception):
    def __init__(self, message, line=None, col=None):
        self.message = message
        self.line = line
        self.col = col
        super().__init__(self.format())

    def format(self):
        loc = ""
        if self.line is not None:
            loc = f" at line {self.line}"
            if self.col is not None:
                loc += f", col {self.col}"
        return f"{self.__class__.__name__}: {self.message}{loc}"


class LexError(MCLError):
    pass


class ParseError(MCLError):
    pass


class TypeError_(MCLError):
    pass


class ShapeError(MCLError):
    pass
