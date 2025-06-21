from typing import Generator, TypeVar, Any

ItemType = TypeVar('T')
class RandomAccessor:
    def __init__(self, generator: Generator[ItemType, None, None]):
        self.generator = generator
        self.cached = []
    
    def __getitem__(self, index: int):
        while index >= len(self.cached):
            self.cached.append(self.generator())
        return self.cached[index]