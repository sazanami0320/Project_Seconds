
from typing import List, Dict, Optional, Any
import json

from exception import SourcedException

class ASTBuilder:
    ''' For obvious reasons, the genkou/scenario of our game should be imperative;
        And for the same reasons, the script should also be imperative.
        However, there are inevitably some redundant or inferrable infomation in the script, 
        which can be a Odysssey for the playwrights if they have to write it through every line.
        Also, composers and voice actors(actually AI though) need to access the state of stage frequently.
        As the result, I decided to write a IR which traverse through every single line and record their states.
        However, it turns out that nobody need a simple ST without details, so I combined that IR into AST to
        eliminate extra passes.
        Short version: AST tracks stage change. It is even not an AST actually, so why not.'''

    def __init__(self):
        self.content = []
        self.bg = 'black'
        self.characters = {}

    def comment(self, src: str, comment: str):
        self.content.append({
            'type': 'comment',
            'src': src,
            'content': comment
        })

    def line(self, src: str, jinbutsu: str, serifu: str, alias: Optional[str]=None, hyojyo: Optional[str]=None, systems: Optional[List[Any]]=None):
        if systems is not None:
            self.systems(src, *zip(*systems))
        if hyojyo is not None: # Alias system.tachie and functions most lately
            self.systems(src, 'tachie', (jinbutsu, hyojyo))
        # We should keep the body short and stout to spare disk usage and make it more readable.
        # And if you know what I mean, no, this is a coffee machine.
        line = {
            'type': 'line',
            'bg': self.bg,
            'src': src,
            'id': jinbutsu,
            'line': serifu,
        }
        if self.characters:
            line['charas'] = self.characters.copy()
        if alias is not None:
            line['alias'] = alias
        self.content.append(line)
    
    def systems(self, src: str, responsibles: str | List[str], works: Any):
        if isinstance(responsibles, str):
            responsibles = [responsibles]
            works = [works]
        if len(self.content) > 0 and self.content[-1]['type'] == 'systems':
            target = self.content[-1]['contents']
        else:
            target = []
            self.content.append({
                'type': 'systems',
                'contents': target
            })
        for responsible, work in zip(responsibles, works):
            if responsible == 'tachie':
                chara, expression = work
                self.characters[chara] = expression
                work = {
                    'id': chara,
                    'exp': expression
                }
            elif responsible == 'background' or responsible == 'cg':
                self.bg = work
            elif responsible == 'hide':
                if work == '全部': 
                    self.characters.clear()
                else:
                    if work in self.characters:
                        self.characters.pop(work)
                    else:
                        raise SourcedException(src, f"Trying to hide {work}'s tachie, who is not even on stage!")
            target.append({
                'type': responsible,
                'src': src,
                'content': work,
            })

    def finish(self) -> List[Dict]:
        content = self.content
        self.content = None
        return content
    
class ASTScript:
    ext = 'json'
    def encode(self, script):
        return json.loads(script)

    def decode(self, obj):
        return json.dumps(obj, ensure_ascii=False)
