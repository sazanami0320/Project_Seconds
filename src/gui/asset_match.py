from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Button, Label, Tree, tree
from typing import Optional, List

def build_tree(tree_node: tree.TreeNode, tree_dict: dict, depth: int=1, history: List[str]=[]):
    for key, value in tree_dict.items():
        if depth >= 2:
            next_history = history + [key]
        else:
            next_history = history
        if isinstance(value, dict):
            new_node = tree_node.add(key)
            build_tree(new_node, value, depth + 1, next_history)
        elif isinstance(value, list):
            tree_node.add_leaf(f"{key}    {value[0].name}等(+{len(value) - 1})", '_'.join(next_history))
        else:
            tree_node.add_leaf(f"{key}    {value.name}", '_'.join(next_history))

class AssetMatcher(Widget):

    BINDINGS = [
        Binding('enter', 'match_asset', '确认', priority=True),
        ('i', 'ignore_asset', '忽略')
    ]

    class MatchFinish(Message):
        def __init__(self, match_result: dict):
            super().__init__()
            self.match_result = match_result

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.hierarchy = {}
        self.match_set = None
        self.current_match = None
        self.selection = None
        self.match_result = None
        self.disabled = True
    
    def start_match(self, name: str, match_set: set, hierarchy: dict):
        self.match_set = match_set
        self.match_result = {}
        self.hierarchy = hierarchy
        tree = self.query_exactly_one('#asset-match-tree')
        tree.reset(name)
        build_tree(tree.root, hierarchy)
        tree.root.expand()
        self.next_match()
        self.disabled = False

    def next_match(self):
        if self.match_set:
            self.current_match = self.match_set.pop()
            self.log(self.current_match)
            self.query_exactly_one('#asset-match-label').update(f"请为{self.current_match}选取对应资源")
        else:
            self.disabled = True
            self.post_message(self.MatchFinish(self.match_result))
            
    def compose(self) -> ComposeResult:
        yield Label('', id='asset-match-label', classes='primary')
        yield Tree('asset_tree', id='asset-match-tree')
        with Horizontal():
            yield Button('忽略', id='asset-match-btn-ignore', classes='cancel-btn', action="self.ignore_asset")
            yield Button('确认', id='asset-match-btn-confirm', classes='confirm-btn', variant='success', action="self.match_asset")

    def on_tree_node_highlighted(self, msg: Tree.NodeHighlighted):
        self.selection = msg.node.data
        self.query_exactly_one('#asset-match-btn-confirm').disabled = self.selection is None
        self.refresh_bindings()

    def check_action(self, action: str, _parameters):
        if action == 'match_asset':
            return None if self.selection is None else True
        return True

    def action_match_asset(self):
        self.match_result[self.current_match] = self.selection
        self.next_match()
    
    def action_ignore_asset(self):
        self.next_match()
