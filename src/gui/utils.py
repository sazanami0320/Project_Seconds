from analyzer import HomoSapiensText, TSSL, ASTScript
from core import WORKSPACE, CONFIG_DIR, analyze, output_tokens
from index import get_index
from ir import Unbabel
from pathlib import Path
from functools import partial, wraps

def to_ast(target_folder: Path):
    proj_name = target_folder.stem
    objs = []
    sources = []
    for target_file in target_folder.iterdir():
        if target_file.suffix == '.txt' or target_file.suffix == '.vbs':
            sources.append(target_file)
            objs.append(analyze(proj_name, target_file, TSSL))
    output_folder = WORKSPACE / 'output' / proj_name
    if not output_folder.exists():
        output_folder.mkdir(parents=True)
    titles = list(map(lambda path: path.stem, sources))
    output_tokens(HomoSapiensText(), objs, titles, output_folder / f"{proj_name}.txt", count=True)
    output_tokens(ASTScript(), objs, titles, output_folder / f"{proj_name}_ast.json")
    return objs, titles

def to_ir(proj_name: str, objs: list, titles: list, suppress_level: int, ask_hook):
    asset_index = get_index(WORKSPACE / 'assets')
    ir_compiler = Unbabel(CONFIG_DIR / proj_name, asset_index)
    def expand_map_key_wrapper(func: callable):
        def expand_map_key(map: dict):
            result = {}
            for key, value in map.items():
                if key[0] in result:
                    result[key[0]][key[1]] = value
                else:
                    result[key[0]] = {key[1]: value}
            return result
        def wrapper(*args, **kwargs):
            return expand_map_key(func(*args, **kwargs))
        return wrapper
    hooks = {
        'ask_bg': partial(ask_hook, '背景', {'背景': asset_index['bg'], 'CG': asset_index['cg']}),
        'ask_cg': partial(ask_hook, 'CG', {'CG': asset_index['cg'], '背景': asset_index['bg']}),
        'ask_fg': expand_map_key_wrapper(partial(ask_hook, '立绘', {'角色表情': asset_index['fg']})),
        'ask_se': partial(ask_hook, '音效', {'音效': asset_index['se']}),
    }
    objs = ir_compiler(objs, titles, suppress_level=suppress_level, **hooks)
