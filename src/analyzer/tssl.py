from .ast import ASTBuilder
from typing import Optional

class TSSL:
    '''Tadshi's Simple Script Lang'''
    ext = 'vbs'
    def __init__(self, mapper):
        super().__init__()
        self.mapper = mapper
        self.chara_id_counter = 0

    # Standard makes sure that jinbutsu_str has no spaces
    def parse_jinbutsu(self, jinbutsu_str: str):
        state = 0
        name = None # Actually this is ID
        alias = None
        expression = None
        for c in jinbutsu_str:
            if state == 0: # Hajime
                if c == '<':
                    state = 2
                    alias = ''
                else:
                    state = 1
                    name = c
            elif state == 1: # Parsing Raw Name:
                if c == '(':
                    state = 4
                    expression = ''
                elif c == '<':
                    state = 2
                    alias = ''
                else:
                    name += c
            elif state == 2: # Parsing alias
                if c == '>':
                    state = 3
                else:
                    alias += c
            elif state == 3: # Name and alias parse finished
                if c == '(':
                    state = 4
                    expression = ''
                else:
                    raise RuntimeError(f"Fail to parse Jinbutsu String {jinbutsu_str}.")
            elif state == 4: # Start parsing Hyojo
                if c == ')':
                    state == 'CLOSED'
                else:
                    expression += c
            else:
                raise RuntimeError(f"WTH?")
        if name is None:
            self.chara_id_counter += 1
            name = f"_{self.chara_id_counter}" # We do not map this
        elif name in self.mapper:
            name = self.mapper[name]
        return name, alias, expression
    
    def parse_system(self, sub_system_str: str):
        if '=>' in sub_system_str: # Legacy 
            equal_sign = '=>'
        elif '=' in sub_system_str:
            equal_sign = '='
        elif ':' in sub_system_str:
            equal_sign = ':'
        else:
            equal_sign = None
        if equal_sign:
            left, right = sub_system_str.split(equal_sign)
            left = left.strip()
            right = right.strip()
        else:
            left = 'tachie'
            right = sub_system_str

        if left == 'tachie':
            character, alias, expression = self.parse_jinbutsu(right)
            if alias is not None:
                raise RuntimeError("Cannot use alias in tachie command!")
            assert expression is not None, sub_system_str
            right = (character, expression)
        elif right in self.mapper:
            right = self.mapper[right]
        return left, right
        
    
    def parse_systems(self, system_str: str):
        assert(system_str.startswith('[') and system_str.endswith(']')), system_str
        return [self.parse_system(sub_system_str.strip()) for sub_system_str in system_str[1:-1].split(',')] 

    def encode(self, script: str, filename: str):
        lines = script.splitlines()
        builder = ASTBuilder()
        for lineno, line in enumerate(lines):
            self.lineno = lineno + 1
            src = f"{filename}:{self.lineno}"
            line = line.strip()
            if len(line) == 0:
                continue
            elif line.startswith(';'):
                if line.startswith(';;'): # Omote comment
                    builder.comment(src, line[2:].strip())
            elif line.startswith('['):
                assert line.endswith(']') # Butai Shikake
                lefts, rights = zip(*self.parse_systems(line))
                builder.systems(src, lefts, rights)
            else:
                spilt_point = line.index(' ')
                jinbutsu = line[:spilt_point]
                chara, alias, expression = self.parse_jinbutsu(jinbutsu)

                serifu = line[spilt_point + 1:]
                systems = None
                if serifu.endswith(']'):
                    spilt_point = serifu.index('[')
                    system_str = serifu[spilt_point:]
                    systems = self.parse_systems(system_str)
                    serifu = serifu[:spilt_point]
                builder.line(src, chara, serifu, alias, expression, systems)
        return builder.finish()
    
    def decode(self, obj):
        raise NotImplementedError('Touching Fish...')
    
