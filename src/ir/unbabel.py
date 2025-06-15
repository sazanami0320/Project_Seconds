'''The Babel Trench to merge the gap between scripts and scenario.
    It turns out that a good amateur VN writer should be a good coder. What a joke.'''
from typing import Optional
from pathlib import Path
import json
from .propmt_ask import ask_bg, ask_cg, ask_fg, ask_se
from exception import SourcedException

DEFAULT_HOOKS = {
    'ask_bg': ask_bg,
    'ask_cg': ask_cg,
    'ask_fg': ask_fg,
    'ask_se': ask_se
}

class Unbabel:
    
    def __init__(self, map_path: Path, index: dict):
        self.result = None
        self.map_path = map_path
        with map_path.open('r', encoding='utf-8') as f:
            config = json.load(f)
        self.chara_map = config['_name2id']
        self.bg_map = config['bg2id']
        self.cg_map = config['cg2id']
        self.fg_map = config['fg2id']
        self.se_map = config['se2id']
        self.asset_index = index
        self._expand_index()
    
    def _expand_index(self):
        def travese_asset_dict(target: dict):
            result = set()
            for key, value in target.items():
                if isinstance(value, dict):
                    result.update(travese_asset_dict(value))
                else:
                    result.add(key) # TODO: Decide whether use full name or splitted name as entry
            return result
        self.bg_set = travese_asset_dict(self.asset_index['bg'])
        self.fg_set = travese_asset_dict(self.asset_index['fg'])
        self.cg_set = travese_asset_dict(self.asset_index['cg'])
        self.se_set = travese_asset_dict(self.asset_index['se'])

    def _map_chara(self, raw_chara_id: str) -> str:
        if raw_chara_id in self.chara_map:
            return self.chara_map[raw_chara_id]
        else:
            return raw_chara_id

    def _map_bg(self, raw_bg: str, try_cg: bool=True) -> Optional[str]:
        if raw_bg in self.bg_set:
            return raw_bg
        elif raw_bg in self.bg_map:
            return self.bg_map[raw_bg]
        elif try_cg and raw_bg in self.cg_set:
            return raw_bg
        elif try_cg and raw_bg in self.cg_map:
            return self.cg_map[raw_bg]
        else:
            return None
        
    def _map_cg(self, raw_cg: str, try_bg: bool=True) -> Optional[str]:
        if raw_cg in self.cg_set:
            return raw_cg
        elif raw_cg in self.cg_map:
            return self.cg_map[raw_cg]
        elif try_bg and raw_cg in self.bg_set:
            return raw_cg
        elif try_bg and raw_cg in self.bg_map:
            return self.bg_map[raw_cg]
        else:
            return None
                
    def _map_fg(self, chara_id: str, expression: str) -> Optional[str]:
        if expression in self.fg_set: # This should not be used.
            print(f"Warning: {expression} escaped mapping as expression.")
            return expression
        elif chara_id in self.fg_map and expression in self.fg_map[chara_id]:
            return self.fg_map[chara_id][expression]
        else:
            return None
        
    def _map_se(self, raw_se: str) -> Optional[str]:
        if raw_se in self.se_set:
            return raw_se
        elif raw_se in self.se_map:
            return self.se_map[raw_se]
        else:
            return None

    def _pass(self, obj, dry_run: bool=True, suppress_level: int=0):
        result = []
        if dry_run:
            unmapped_background = set()
            unmapped_cg = set()
            unmapped_expression = set()
            unmapped_sound = set()
        for item in obj:
            if item['type'] == 'comment':
                if not dry_run:
                    result.append(item)
            elif item['type'] == 'line':
                if dry_run:
                    # We need not check bg or charas field 'cause they are copy of system instr's counterparts.
                    # Also, they are redundant fields used in the AST stage.
                    continue
                mapped_item = {
                    'type': 'line',
                    'src': item['src'],
                    'id': item['id'],
                    'cid': self._map_chara(item['cid']),
                    'line': item['line']
                }
                if 'alias' in item:
                    mapped_item['alias'] = item['alias']
                result.append(mapped_item)
            elif item['type'] == 'systems':
                mapped_systems = []
                for system_item in item['contents']:
                    system_type = system_item['type']
                    content = system_item['content']
                    if system_type == 'background':
                        content = self._map_bg(content)
                        if content is None and dry_run:
                            unmapped_background.add(system_item['content'])
                    elif system_type == 'cg':
                        content = self._map_cg(content)
                        if content is None and dry_run:
                            unmapped_cg.add(system_item['content'])
                    elif system_type == 'sound':
                        content = self._map_se(content)
                        if content is None and dry_run:
                            unmapped_sound.add(system_item['content'])
                    elif system_type == 'tachie':
                        id = self._map_chara(content['cid'])
                        exp = self._map_fg(id, content['exp'])
                        if exp is not None:
                            content = { 'cid': id, 'exp': exp }
                        else:
                            if dry_run:
                                unmapped_expression.add((id, content['exp']))
                            content = None
                    else:
                        # We do not map other resources, at least for now.
                        pass
                    if dry_run:
                        continue
                    if content is None:
                        if suppress_level == 0:
                            raise SourcedException(system_item['src'], f"无法映射{system_type}类型的{system_item['content']}。")
                        elif suppress_level == 1:
                            if system_type == 'tachie':
                                content = { 'cid': self._map_chara(system_item['content']['cid']), 'exp': f"<{system_item['content']['exp']}>" }
                            else:
                                content = f"<{system_item['content']}>"
                        elif suppress_level == 2:
                            if system_type == 'tachie':
                                content = { 'cid': self._map_chara(system_item['content']['cid']), 'exp': system_item['content']['exp'] }
                            else:
                                content = system_item['content']
                        elif suppress_level == 3:
                            continue
                        else:
                            raise RuntimeError(f"Invalid suppress level {suppress_level}")
                    mapped_systems.append({
                        'type': system_type,
                        'src': system_item['src'],
                        'content': content
                    })
                # If dry run the len is 0
                if len(mapped_systems) > 0:
                    result.append({
                        'type': 'systems',
                        'content': mapped_systems
                    })
            else:
                # This is a system-level fault.
                raise RuntimeError(f"Cannot recognize item of type {item['type']}.")
        if dry_run:
            return unmapped_background, unmapped_cg, unmapped_expression, unmapped_sound
        else:
            return result
        
    def _save_maps(self):
        with self.map_path.open('w', encoding='utf-8') as f:
            json.dump({
                '_name2id': self.chara_map,
                'bg2id': self.bg_map,
                'cg2id': self.cg_map,
                'fg2id': self.fg_map,
                'se2id': self.se_map
            }, f, indent=4, sort_keys=True, ensure_ascii=False)


    def __call__(self, *args, **kwds) -> bool:
        objs, = args
        if 'suppress_level' in kwds:
            suppress_level = kwds['suppress_level']
            kwds.pop('suppress_level')
        else:
            suppress_level = 0
        hooks = DEFAULT_HOOKS.copy()
        hooks.update(kwds)
        ump_sets = (set(), set(), set(), set())
        for obj in objs:
            for old, new in zip(ump_sets, self._pass(obj, dry_run=True)):
                old.update(new)
        ump_bg, ump_cg, ump_fg, ump_se = ump_sets
        if ump_bg:
            new_bg_map = hooks['ask_bg'](ump_bg)
            if new_bg_map:
                self.bg_map.update(new_bg_map)
        if ump_cg:
            new_cg_map = hooks['ask_cg'](ump_cg)
            if new_cg_map:
                self.cg_map.update(new_cg_map)
        if ump_fg:
            new_fg_map = hooks['ask_fg'](ump_fg)
            if new_fg_map:
                for new_key, new_value in new_fg_map.items():
                    if new_key in self.fg_map:
                        self.fg_map[new_key].update(new_value)
                    else:
                        self.fg_map[new_key] = new_value
        if ump_se:
            new_se_map = hooks['ask_se'](ump_se)
            if new_se_map:
                self.se_map.update(new_se_map)
        self._save_maps()
        return [self._pass(obj, dry_run=False, suppress_level=suppress_level) for obj in objs]
        