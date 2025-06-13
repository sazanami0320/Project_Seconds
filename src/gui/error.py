from textual.app import RenderResult
from textual.reactive import reactive
from textual.widgets import Static
from textual.message import Message
from rich.markup import escape

from core import read_script
from exception import SourcedException

class Error(Static):
    content = reactive('加载中')
    BINDINGS = [
        ('R', 'retry', '重试'),
        ('C', 'cancel', '取消')
    ]   

    class FailMessage(Message):
        pass

    class RetryMessage(Message):
        pass

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.script_dir = None

    def render(self) -> RenderResult:
        return self.content
    
    def action_retry(self):
        self.post_message(self.RetryMessage())

    def action_cancel(self):
        self.post_message(self.FailMessage())
    
    def report_sourced_error(self, error: SourcedException):
        content = ':warning:[bold red]Error found during compiling:[/]\n'
        name, line = error.src.split(':')
        sources = []
        for script_file in self.script_dir.iterdir():
            if script_file.stem == name:
                sources = read_script(script_file).split('\n')
        if sources:
            start = min(1, line - 2) - 1
            end = max(len(sources), line + 2) - 1
            for report_line in range(start, end + 1):
                if report_line == line:
                    content += f"  [red]>|{escape(report_line)}[/red]\n"
                else:
                    content += f"   |{escape(report_line)}\n"
        content += error.__str__
        self.content = content
        
