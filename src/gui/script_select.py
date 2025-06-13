from textual.app import ComposeResult
from textual.message import Message
from textual.widgets import Button, Static, Label, RadioSet
from textual.reactive import reactive
from core import SCRIPT_DIR
from pathlib import Path

class ScriptSelect(Static):
    options = reactive([])
    BINDINGS = [('N', 'go_on', '下一步')]

    class ScriptSelected(Message):
        def __init__(self, script_dir: Path):
            self.script_dir = script_dir
            super().__init__()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.options = list(map(lambda dir: dir.stem, filter(lambda path: path.is_dir(), SCRIPT_DIR.iterdir())))

    def action_go_on(self):
        selection = self.options[self.query_exactly_one('#script-radio-set').pressed_index]
        self.post_message(self.ScriptSelected(SCRIPT_DIR / selection))
        
    def compose(self) -> ComposeResult:
        yield Label("请选择一个剧本：")
        yield RadioSet(*self.options, id='script-radio-set')
        yield Button(label="下一步", classes='btn-confirm', action='go_on')
        
    def on_mount(self):
        self.query_exactly_one(RadioSet).focus()
