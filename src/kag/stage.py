from typing import List, Dict, Callable
import random

# This is much harder then I had thought of
class StageCommand:
    def __init__(self, cmd_type: str, chara_id: str, command: any):
        self.command_type = cmd_type
        self.commands = {chara_id: command}

    def append(self, chara_id: str, command: any):
        self.commands[chara_id] = command

class Stage:
    '''The very class for all tachie formatting works.
       In other words, this is the manager for the front layers'''
    def __init__(self, stage_markers: List[List[int]], heights: Dict[str, Dict[int, int]], asset_index: Dict[str, dict], writeln: Callable[[str], None], antei_level: int=2, seed=1234):
        # Tachies of different stance and distance share the same markers
        self.markers = stage_markers
        self.antei_level = antei_level
        self.chara_heights = heights
        self.writeln = writeln
        # Lazy!
        self.occupation_mode = 0
        self.stage_occupation = [None]
        # Volatile!
        self.current_stage = {}
        self.current_kyori = {}
        # Let's try laycopy and freeimage, alright?
        # self.layer_map = {}
        self.stance_counter = {}
        self.stance_record = {}
        self.stack = []
        self.asset_index = asset_index
        random.seed(seed)

    def stack_command(self, command_type: str, chara_id: str, command: str):
        if len(self.stack) > 0 and self.stack[-1].command_type == command_type:
            self.stack[-1].append(chara_id, command)
        else:
            self.stack.append(StageCommand(command_type, chara_id, command))

    def parse_chara_command(self, chara_id: str, exp_id: str, kyori: str='mid'):
        command = (exp_id, kyori)
        if chara_id not in self.current_stage:
            self.stack_command('create', chara_id, command)
            self.current_stage[chara_id] = exp_id
            self.current_kyori[chara_id] = kyori
        elif self.current_stage[chara_id] != exp_id or self.current_kyori[chara_id] != kyori:
            self.stack_command('update', chara_id, command)
            self.current_stage[chara_id] = exp_id
            self.current_kyori[chara_id] = kyori
            # self.chara_show_up(chara_id, exp_id, kyori, render)
        else:
            # Check stance
            stance_count = self.stance_counter[chara_id]
            if stance_count >= random.randint(3, 6):
                self.stance_counter[chara_id] = 0
                self.stack_command('update', chara_id, None)

    def parse_hide_command(self, chara_id: str):
        self.stack_command('delete', chara_id, None)
        self.current_stage.pop(chara_id)
        self.current_kyori.pop(chara_id)

    def _run_stack(self, render: bool=True):
        command_capsule = []
        for stage_command in self.stack:
            if stage_command.command_type == 'create':
                self._charas_show_up(command_capsule, stage_command.commands)
            elif stage_command.command_type == 'update':
                self._charas_update(command_capsule, stage_command.commands)
            elif stage_command.command_type == 'delete':
                self._charas_leave(command_capsule, stage_command.commands)
            else:
                raise RuntimeError('Impossible')
        self.stack.clear()
        if render:
            for command_line in command_capsule:
                self.writeln(command_line)
    
    def _charas_show_up(self, command_capsule: List[str], commands: Dict[str, any]):
        old_pos_dict = {}
        for layer_index, chara_id in enumerate(self.stage_occupation):
            if chara_id is not None:
                old_pos_dict[chara_id] = (layer_index, self.markers[self.occupation_mode])
        # Pass One: Occupy empty spaces.
        for chara_id, (exp_id, kyori) in commands.items():
            if chara_id not in self.stage_occupation:
                # Find a place for our new enjya!
                if  None in self.stage_occupation:
                    # There are empty slots
                    empty_index = 0
                    while self.stage_occupation[empty_index] is not None:
                        empty_index += 1
                    self.stage_occupation[empty_index] = chara_id
                else:
                    self.occupation_mode += 1
                    if self.occupation_mode > 7: # layer 7 is reserved for something like `speaker layer`
                        raise RuntimeError('NVLMaker: we have no room for so many of them!')
                    self.stage_occupation.append(chara_id)
        # And deal with charas which are already present
        # This action will not change layer index so we need not to check it
        wm_count = 0
        for chara_id, (layer_index, old_pos) in old_pos_dict.items():
            new_pos = self.markers[self.occupation_mode][layer_index]
            # TODO: Support kyori
            if old_pos != new_pos:
                command_capsule.append(f"@move time=\"200\" path=\"({new_pos}, {self.chara_heights[chara_id]}, 255)\" "
                                       f"layer=\"{layer_index}\"")
                wm_count += 1
        command_capsule.extend(['@wm'] * wm_count)
        command_capsule.append('@backlay')
        # Pass 2: Show up characters in one change.
        for chara_id, (exp_id, kyori) in commands.items():
            layer_index = self.stage_occupation.index(chara_id)
            chara_pos = self.markers[self.occupation_mode][layer_index]
            # This line depends on the naming strategy of fg asset, which is not a good choice.
            # TODO: Add kyori information into it.
            fg_file = random.choice(self.asset_index['fg'][chara_id][exp_id])
            self.stance_record[chara_id] = fg_file.name
            self.stance_counter[chara_id] = 0
            command_capsule.append(f"@image left=\"{chara_pos}\" page=\"back\" layer=\"{layer_index}\" "
                                    f"top=\"{self.chara_heights[chara_id]}\" storage=\"{fg_file.stem}\" visible=\"true\"")
        command_capsule.append('@trans time="500" method="crossfade"')
        command_capsule.append("@wt")
                
    def _charas_update(self, command_capsule: List[str], commands: Dict[str, any]):
        command_capsule.append('@backlay')
        for chara_id, command in commands.items():
            layer_index = self.stage_occupation.index(chara_id)
            chara_pos = self.markers[self.occupation_mode][layer_index]
            if command is None:
                exp_id = self.current_stage[chara_id]
                current_fg_full_name = self.stance_record[chara_id]
                possible_fgs = list(filter(lambda fg: fg.name != current_fg_full_name, self.asset_index['fg'][chara_id][exp_id]))
                if len(possible_fgs) == 0:
                    self.stance_counter[chara_id] = 0
                    continue
                # TODO: Add kyori information into it.
                fg_file = random.choice(possible_fgs)
            else:
                exp_id, kyori = command
                fg_file = random.choice(self.asset_index['fg'][chara_id][exp_id])
            self.stance_record[chara_id] = fg_file.name
            self.stance_counter[chara_id] = 0
            command_capsule.append(f"@image left=\"{chara_pos}\" page=\"back\" layer=\"{layer_index}\" " 
                            f"top=\"{self.chara_heights[chara_id]}\" storage=\"{fg_file.stem}\" visible=\"true\"")
        command_capsule.append('@trans time="500" method="crossfade"')
        command_capsule.append("@wt")
            
    
    def _charas_leave(self, command_capsule: List[str], commands: Dict[str, any]):
        old_pos_dict = {}
        for layer_index, chara_id in enumerate(self.stage_occupation):
            if chara_id is None:
                continue
            old_pos_dict[chara_id] = (layer_index, self.markers[self.occupation_mode])
        command_capsule.append('@backlay')
        for chara_id in commands.keys():
            layer_index = self.stage_occupation.index(chara_id)
            if self.occupation_mode >= self.antei_level:
                self.occupation_mode -= 1
                self.stage_occupation.pop(layer_index)
            else:
                self.stage_occupation[layer_index] = None
            command_capsule.append(f"@freeimage layer=\"{layer_index}\" page=\"back\"")
        command_capsule.append('@trans method="crossfade" time="500"')
        command_capsule.append("@wt")
        wm_count = 0
        for new_layer_index, chara_id in enumerate(self.stage_occupation):
            if chara_id is None:
                continue
            old_layer_index, old_pos = old_pos_dict[chara_id]
            new_pos = self.markers[self.occupation_mode][new_layer_index]
            if old_layer_index != new_layer_index:
                command_capsule.append(f"@copylay destlayer=\"{new_layer_index}\" srclayer=\"{old_layer_index}\"")
                command_capsule.append(f"@freeimage layer={old_layer_index}")
            if old_pos != new_pos:
                command_capsule.append(f"@move time=200 path=\"({new_pos}, {self.chara_heights[chara_id]}, 255)\" "
                                       f"layer=\"{new_layer_index}\"")
                wm_count += 1
        command_capsule.extend(['@wm'] * wm_count)

    def render_on_back(self):
        for layer_index, (chara_id, pos) in enumerate(zip(self.stage_occupation, self.markers[self.occupation_mode])):
            if chara_id is None:
                continue
            exp_id = self.current_stage[chara_id]
            fg_file = random.choice(self.asset_index['fg'][chara_id][exp_id])
            self.stance_counter[chara_id] = 0
            self.writeln(f"@image left=\"{pos}\" page=\"back\" layer=\"{layer_index}\" "
                            f"top=\"{self.chara_heights[chara_id]}\" storage=\"{fg_file.stem}\" visible=\"true\"")

    def clear_fg(self, page: str='back'):
        for layer_index, chara_id in enumerate(self.stage_occupation):
            if chara_id is not None:
                self.writeln(f"@freeimage layer=\"{layer_index}\" page=\"{page}\"") 
    
    def reset_record(self):
        self.occupation_mode = 0
        self.stage_occupation = [None]
        self.current_stage.clear()
        self.current_kyori.clear()
        self.stance_counter.clear()
        self.stance_record.clear()
        self.stack.clear()

    def tick_line(self, speaker_id: str, render=True):
        for key in self.stance_counter.keys():
            self.stance_counter[key] = self.stance_counter[key] + 1
        if len(self.stack) > 0:
            self._run_stack(render)
        # TODO: Add facial expressions
