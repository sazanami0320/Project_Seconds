from textual.app import RenderResult
from textual.reactive import reactive
from textual.widgets import Static

class Alarm(Static):
    content = reactive('')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def render(self) -> RenderResult:
        return self.content
        
