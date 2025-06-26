from pathlib import Path
import json
from typing import Optional

def prompt_dump_ask(ask_class:str, unsatisfied: set):
    dump_target = input(f"Please give a dir for {ask_class}.(default: output/{ask_class}.json)\n")
    if not dump_target:
        dump_target = f"output/{ask_class}.json"
    dump_target = Path(dump_target).resolve()
    if ask_class == 'fg':
        dump = {}
        for id, exp in unsatisfied:
            if id in dump:
                dump[id][exp] = ''
            else:
                dump[id] = {exp: ''}
    elif ask_class == 'voice':
        dump = list(map(lambda pair: [pair[0], pair[1]], sorted(unsatisfied)))
    else:
        dump = {key: '' for key in unsatisfied}
    with dump_target.open('w', encoding='utf-8') as f:
        json.dump(dump, f, indent=4, sort_keys=True, ensure_ascii=False)

def ask_bg(unsatisfied: set) -> Optional[dict]:
    prompt_dump_ask('bg', unsatisfied)
    
def ask_cg(unsatisfied: set) -> Optional[dict]:
    prompt_dump_ask('cg', unsatisfied)

def ask_fg(unsatisfied: set) -> Optional[dict]:
    prompt_dump_ask('fg', unsatisfied)

def ask_se(unsatisfied: set) -> Optional[dict]:
    prompt_dump_ask('se', unsatisfied)

def ask_vc(unsatisfied: set) -> Optional[dict]:
    prompt_dump_ask('voice', unsatisfied)