from textual import on
from textual.app import App, ComposeResult
from textual.containers import VerticalScroll
from textual.widgets import Header, Footer, ContentSwitcher, Static
from pathlib import Path

from exception import SourcedException
from .script_select import ScriptSelect
from .alarm import Alarm
from .error import Error
from .utils import to_ast

GUI_DIR = Path(__file__).resolve().parent


class MakeApp(App):

    BINDINGS = [('q', 'quit', '退出')]

    def __init__(self):
        super().__init__(css_path=GUI_DIR / 'style.tcss')
        self.call_record = None

    def compose(self) -> ComposeResult:
        yield Header()
        with VerticalScroll():
            with ContentSwitcher(initial='src-select', id='main-cs'):
                yield ScriptSelect(id='src-select')
                yield Static('Dummy', id='asset-match')
                yield Alarm(id='alarm')
                yield Error(id='error')
        yield Footer()

    def alarm(self, msg: str):
        self.query_exactly_one(Alarm).content = msg
        self.query_exactly_one('#main-cs').current = 'alarm'
    
    def reset(self):
        self.query_exactly_one('#main-cs').current = 'src-select'
    
    @on(ScriptSelect.ScriptSelected)
    def on_src_selected(self, message: ScriptSelect.ScriptSelected):
        self.alarm(f"正在尝试编译{message.script_dir.stem}...")
        self.query_exactly_one(Error).script_dir = message.script_dir
        # No asyncs for such simple project, plz!
        self.wrapped_call(to_ast, message.script_dir)

    @on(Error.FailMessage)
    def on_fail(self):
        # Reset to step one
        self.reset()

    @on(Error.RetryMessage)
    def on_retry(self):
        # Reset to step one
        self.wrapped_call(self.call_record[0], *self.call_record[1], **self.call_record[2])

    def wrapped_call(self, func, *args, **kwargs):
        self.query_exactly_one(Error).content = '加载中'
        self.call_record = (func, args, kwargs)
        try:
            func(*args, **kwargs)
        except SourcedException as e:
            self.query_exactly_one(Error).report_sourced_error(e)
            self.query_exactly_one('#main-cs').current = 'error'
        else:
            self.alarm("操作成功。")
            self.set_timer(3, self.reset)

    def ask_hook(self, hierarchy):
        self.query_exactly_one('#main-cs').current = 'asset-match'
