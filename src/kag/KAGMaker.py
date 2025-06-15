from core import OUTPUT_DIR
from pathlib import Path

class KAGMaker:
    def __init__(self):
        self.kag_lines = None
        # A set of used chara ids i.e. tags.
        # List can keep the order of charas.
        self.chara_list = []
        # A dynamically-updated map from chara id to their current (storage, pos, layer).
        self.tachie_map = {}
        self.current_speaker = None
        self.cg_mode = False # Whether we are showing a CG.
    
    def __call__(self, *args, **kwds):
        proj_name, irs, names = args
        self.tachie_map.clear()
        line_indent = kwds['line_indent'] if 'line_indent' in kwds else 4
        for ir, name in zip(irs, names):
            output_path = OUTPUT_DIR / proj_name / f"{name}.ks"
            self.kag_lines = []
            self.writeln(f"*{name}|{name}")
            for item in ir:
                if item['type'] == 'comment':
                    self.writeln(f";[剧本注]{item['content']}")
                elif item['type'] == 'line':
                    chara_id = item['cid']
                    if chara_id.startswith('$'): # Take this as an NPC
                        self.writeln(f"@npc {item['alias']}")
                    else:
                        if chara_id not in self.chara_list:
                            self.chara_list.append(chara_id)
                        if 'alias' in item:
                            # namelist.tjs actually compiles into npc macros.
                            # So as long as we do not play with fontcolor, this is correct:
                            chara_command = f"@npc {item['alias']}"
                        else:
                            chara_command = f"@{chara_id}"
                        if chara_id in self.tachie_map:
                            # TODO: Maybe add facial expression in the future?
                            # chara_command += f" face=\"{self.tachie_map[chara_id][0]}\""
                            pass
                        if chara_command != self.current_speaker:
                            self.writeln(chara_command)
                            self.current_speaker = chara_command
                    self.writeln(f"{' ' * line_indent}{item['line']} [w]") # default w
                elif item['type'] == 'systems':
                    for system_item in item['content']:
                        self.compile_system(system_item)
            with output_path.open('w', encoding='utf-8') as f:
                f.writelines(self.kag_lines)
        # Try to generate a namelist for futher edit. Is this really necessary?
        with open(OUTPUT_DIR / proj_name / 'namelist.tjs', 'w', encoding='utf-8') as f:
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
        self.kag_lines = None

    def compile_system(self, system: dict):
        # Dirty works now, guys.
        # We try to convert some simple instr here.
        # However, only C.E. (maybe 773 now) can know WTH these things should be really compiled as.
        # If we could not handle some system command we just mark it in the ks file.
        system_type = system['type']
        content = system['content']
        if system_type == 'background':
            self.writeln(f"@bg storage={self.resource_name(content)}")
            if self.cg_mode:
                self.exit_cg_mode()
        elif system_type == 'cg':
            if not self.cg_mode:
                self.enter_cg_mode()
            self.writeln(f"@bg storage={self.resource_name(content)}")
        elif system_type == 'sound':
            self.writeln(f"@se storege={self.resource_name(content)}")
        elif system_type == 'tachie':
            self.chara_show_up(content['cid'], content['exp'])
        elif system_type == 'hide':
            if content == 'all':
                self.writeln('@clfg')
                self.tachie_map.clear()
            else:
                self.chara_leave(content)
        elif system_type == 'reset':
            if content == 'cg':
                self.exit_cg_mode()
            elif content == 'sound':
                self.writeln('@stopse')
            else: # e.g. zoom effect
                self.writeln(f";[需求]重置{content}")
        else: # Transforms, move of focus, and many others:
            self.writeln(f";[需求]{system_type} = {content}")
        

    def enter_cg_mode(self):
        assert not self.cg_mode
        self.writeln('@clfg')
        self.cg_mode = True
    
    def exit_cg_mode(self):
        assert self.cg_mode
        self.render_tachie()
    
    # TODO: Write and test these functions
    # These functions are harder then I thought so is marked as TODO
    # Idea: all characters make use of the whole screen
    # When a new chara shows up all existing charas are pushed left
    # But when a chara leaves other characters do not change their pos
    # This should handle most cases, leaving scriptor to fine-tune.
    # We should maintain every chara's expression, pos and layer.
    # Every character should have their own heights and that should be 
    # written into some file.
    def render_tachie(self):
        available_width = 1200
        default_height = 200 # This should read from a config

    def chara_show_up(self, character: str, fg_name: str):
        # Some logics
        if not self.cg_mode:
            self.render_tachie() # Will this work? I dunno

    def chara_leave(self, character: str):
        # Some logics
        if not self.cg_mode:
            self.render_tachie()

    # It's a simple replace for now.
    # If necessary, it should look up resource in the asset index 
    # and generate the resource name via Path object.
    def resource_name(self, name: str):
        return name.replace('_', ' ')

    def writeln(self, line: str):
        self.kag_lines.append(f"{line}\n")