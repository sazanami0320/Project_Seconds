from textual import on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.message import Message
from textual.widgets import Button, Static, Label, OptionList, RadioSet, RadioButton
from textual.reactive import reactive
from core import SCRIPT_DIR
from pathlib import Path

class ScriptSelect(Static):
    options = reactive([])
    BINDINGS = [Binding('enter', 'go_on', '下一步', priority=True)]

    class ScriptSelected(Message):
        def __init__(self, script_dir: Path, suppress_level: int):
            self.script_dir = script_dir
            self.suppress_level = suppress_level
            self.disabled = False
            super().__init__()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.options = list(map(lambda dir: dir.stem, filter(lambda path: path.is_dir(), SCRIPT_DIR.iterdir())))

    def action_go_on(self):
        # This should be triggered only once during each mount
        if self.disabled:
            return
        self.disabled = True
        selection = self.options[self.query_exactly_one('#script-option-list').highlighted]
        suppress_level = self.query_exactly_one('#suppress-radio-set').pressed_index
        self.post_message(self.ScriptSelected(SCRIPT_DIR / selection, suppress_level))

    @on(OptionList.OptionSelected)
    def on_selected(self, message: OptionList.OptionSelected):
        message.stop()
        # This should not be triggered
        self.log('On selected triggered.')
        # self.post_message(self.ScriptSelected(SCRIPT_DIR / selection))
        
    def compose(self) -> ComposeResult:
        yield Label("请选择一个剧本：")
        yield OptionList(*self.options, id='script-option-list')
        yield Label("是否忽略映射缺失：")
        with RadioSet(id='suppress-radio-set'):
            for supress_level, text in enumerate(('不忽略', '忽略但标记', '忽略', '删除无法映射的指令')):
                yield RadioButton(text, supress_level == 0)
        yield Button(label="下一步", classes='btn-confirm', action='go_on')
        
    def on_mount(self):
        self.disabled = False
        self.query_exactly_one(OptionList).focus()
