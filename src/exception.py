class SourcedException(Exception):
    def __init__(self, src, *args):
        self.src = src
        super().__init__(*args)

