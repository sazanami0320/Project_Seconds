from core import OUTPUT_DIR
from pathlib import Path
from .stage import Stage
import json

class KAGMaker:
    def __init__(self, config_dir: Path, asset_index: dict):
        self.kag_lines = None
        # A set of used chara ids i.e. tags.
        # List can keep the order of charas.
        self.chara_list = []
        self.asset_index = asset_index
        self.cg_mode = False # Whether we are showing a CG.
        self.background = None
        with config_dir.open('r', encoding='utf-8') as f:
            self.config = json.load(f)
        markers = self.config['markers']
        heights = self.config['heights']
        self.stage = Stage(markers, heights, asset_index, self.writeln)
        self.transform_cache = None
    
    def __call__(self, *args, **kwds):
        proj_name, irs, names = args
        line_indent = kwds['line_indent'] if 'line_indent' in kwds else 4
        for chapter_index in range(len(irs)):
            name = names[chapter_index]
            output_path = OUTPUT_DIR / proj_name / f"{name}.ks"
            self.kag_lines = []
            self.writeln(f"*start|{name}")
            for item in irs[chapter_index]:
                if item['type'] == 'comment':
                    self.writeln(f";[剧本注]{item['content']}")
                elif item['type'] == 'line':
                    self.pre_line_hook()
                    chara_id = item['cid']
                    self.stage.tick_line(chara_id, render=not self.cg_mode)
                    if chara_id.startswith('$'): # Take this as an NPC
                        self.writeln(f"@npc {item['alias']}")
                    elif chara_id == '旁白':
                        pass
                    else:
                        if chara_id not in self.chara_list:
                            self.chara_list.append(chara_id)
                        if 'alias' in item:
                            # namelist.tjs actually compiles into npc macros.
                            # So as long as we do not play with fontcolor, this is correct:
                            chara_command = f"@npc {item['alias']}"
                        else:
                            chara_command = f"@{chara_id}"
                        self.writeln(chara_command)
                    self.writeln(f"{' ' * line_indent}{item['line']} [w]") # default w
                elif item['type'] == 'systems':
                    for system_item in item['content']:
                        self.compile_system(system_item)
            if chapter_index == len(irs) - 1:
                self.writeln('@jump storage=end.ks')
            else:
                self.writeln(f"@jump storage={names[chapter_index + 1]}.ks")
            with output_path.open('w', encoding='utf-16') as f:
                f.writelines(self.kag_lines)
        # Try to generate a namelist for futher edit. Is this really necessary?
        with open(OUTPUT_DIR / proj_name / 'appendix' / 'namelist.tjs', 'w', encoding='utf-16') as f:
            f.write('(const) [\n')
            for index, chara_tag in enumerate(self.chara_list):
                f.writelines([
                    ' (const) %[\n',
                    '  "name" => "FIXME",\n',
                    '  "face" => "",\n',
                    '  "color" => "0x000000",\n'
                    f"  \"tag\" => \"{chara_tag}\"\n"
                    ' ]'
                ])
                if index < len(self.chara_list) - 1:
                    f.write(',') # In case nvlmaker does not recognize trailing comma
                f.write('\n')
            f.write(']\n')
        with open(OUTPUT_DIR / proj_name / 'appendix' / 'macro_name.ks', 'w', encoding='utf-16') as f:
            f.write('*start\n')
            for index, chara_tag in enumerate(self.chara_list):
                f.writelines([
                    f"[macro name={chara_tag}]\n",
                    f"[npc * id={chara_tag} color=0xffffff80]\n",
                    '[endmacro]\n',
                ])
            f.write('[return]\n')
        
        self.kag_lines = None

    def compile_system(self, system: dict):
        # Dirty works now, guys.
        # We try to convert some simple instr here.
        # Well, I do not expect that I will be responsible of this.
        system_type = system['type']
        content = system['content']
        if system_type == 'background':
            if self.transform_cache:
                transform_cache = self.transform_cache
                self.transform_cache = None
                self.compile_system({'type': 'background', 'content': transform_cache})
            self.background = content
            if self.cg_mode:
                self.writeln(f"@bg storage={content} page=back")
                self.exit_cg_mode()
            else:
                # EXPERIMENTAL!
                self.stage.clear()
                self.writeln(f"@bg storage={content}")
        elif system_type == 'cg':
            if not self.cg_mode:
                self.enter_cg_mode()
            self.writeln(f"@bg storage={content}")
        elif system_type == 'sound':
            self.writeln(f"@se storage={content}")
        elif system_type == 'tachie':
            if content['exp'].startswith('<'):
                return
            self.stage.parse_chara_command(content['cid'], content['exp'].split('_')[1])
        elif system_type == 'hide':
            if content == '全部':
                self.writeln('@clfg')
            else:
                self.stage.parse_hide_command(content)
        elif system_type == 'reset':
            if content == 'cg':
                self.exit_cg_mode()
            elif content == 'sound':
                self.writeln('@stopse')
            else: # e.g. zoom effect
                self.writeln(f";[需求]重置{content}")
        elif system_type == 'transform':
            if content == 'black' or content == 'blackout':
                self.transform_cache = 'black'
            else:
                self.writeln(f";[需求]{system_type} = {content}")
        else: # Transforms, move of focus, and many others:
            self.writeln(f";[需求]{system_type} = {content}")
    
    def pre_line_hook(self):
        if self.transform_cache:
            self.writeln(f"@bg storage={self.transform_cache}")
            self.writeln(f"@bg storage={self.background}")
            self.transform_cache = None

    def enter_cg_mode(self):
        assert not self.cg_mode
        self.writeln('@clfg')
        self.cg_mode = True
    
    def exit_cg_mode(self):
        if not self.cg_mode: # This may occur due to supress_level = 3
            return
        self.stage.render_on_back()
        self.writeln('@trans time=50 method=crossfade')
        self.writeln('@wt')
        self.cg_mode = False

    def writeln(self, line: str):
        self.kag_lines.append(f"{line}\n")