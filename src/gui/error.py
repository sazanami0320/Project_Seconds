from textual.app import RenderResult
from textual.binding import Binding
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Static
from textual.message import Message
from rich.markup import escape
from rich.text import Text

from core import read_scenario
from exception import SourcedException

class Error(Widget):
    BINDINGS = [
        Binding('r', 'retry', '重新编译'),
        Binding('c', 'cancel', '取消')
    ]

    class FailMessage(Message):
        pass

    class RetryMessage(Message):
        pass

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.can_focus = True
        self.scenario_dir = None

    def compose(self):
        yield Static(id='error-msg')
    
    def action_retry(self):
        self.post_message(self.RetryMessage())

    def action_cancel(self):
        self.post_message(self.FailMessage())

    def reset(self):
        self.query_exactly_one('#error-msg').update('加载中')
    
    def report_sourced_error(self, error: SourcedException):
        name, line = error.src.split(':')
        line = int(line)
        sources = []
        for scenario_file in self.scenario_dir.iterdir():
            if scenario_file.stem == name:
                sources = read_scenario(scenario_file).splitlines()
                name = f"{scenario_file}:{line}"
        content = f"[bold red]Error found in {name} during compiling:[/]\n"
        if sources:
            start = max(1, line - 2) - 1
            end = min(len(sources), line + 2) - 1
            for report_line in range(start, end + 1):
                if report_line == line - 1:
                    content += f"[gray]{report_line + 1:4}  >|[/][red]{escape(sources[report_line])}[/red]\n"
                else:
                    content += f"[gray]{report_line + 1:4}   |[/]{escape(sources[report_line])}\n"
        content += error.__str__()
        self.query_exactly_one('#error-msg').update(content)
