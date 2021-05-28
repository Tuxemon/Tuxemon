from io import StringIO

from tuxemon.lib.simplefsm import SimpleFSM

WRD = 0  # word
SPC = 1  # whitespace
CMA = 2  # comma
EOF = 3  # end of file
NUL = 4  # empty string; ""


class Lexer:
    """
    Lexer for game script
    """

    word = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_${}().^-:'\"!\\/?<>"
    whitespace = " \t"
    comma = ","
    eof = "ff7a8c0e-2749-4109-b0e4-f377bf81737e"

    def __init__(self, stream):
        if isinstance(stream, str):
            stream = StringIO(stream)
        self.stream = stream
        self.char = ""
        self.state = None
        self.fsm = SimpleFSM(
            (
                (CMA, CMA, CMA, "die"),
                (NUL, WRD, WRD, "store"),
                (NUL, NUL, NUL, "eof"),
                (SPC, CMA, CMA, "die"),
                (SPC, NUL, NUL, "break"),
                (SPC, SPC, SPC, "whitespace"),
                (SPC, WRD, WRD, "break"),
                (WRD, CMA, CMA, "break"),
                (WRD, NUL, NUL, "break"),
                (WRD, SPC, SPC, "break"),
                (WRD, WRD, WRD, "store"),
            ),
            initial=NUL,
        )

    def __iter__(self):
        return self

    def __next__(self):
        token = self.read_token()
        if token == self.eof:
            raise StopIteration
        return token

    def split(self):
        return list(self)

    def read_token(self):
        token = ""
        while True:
            prev_state = self.fsm.state
            if self.char == "":
                self.char = self.stream.read(1)
            if self.char == "":
                action = self.fsm(NUL)
            elif self.char in Lexer.word:
                action = self.fsm(WRD)
            elif self.char in Lexer.whitespace:
                action = self.fsm(SPC)
            elif self.char in Lexer.comma:
                action = self.fsm(CMA)
            else:
                raise ValueError(f"unexpected character: {self.char}")
            if "store" == action:
                token += self.char
                self.char = ""
            elif "break" == action:
                break
            elif "eof" == action:
                self.char = ""
                return self.eof
            elif "whitespace" == action:
                token = " "
                self.char = ""
                continue
            else:
                raise ValueError(f"unexpected action: {action}")
        print("token:", prev_state, token)
        return prev_state, token
