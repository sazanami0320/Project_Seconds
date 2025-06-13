from analyzer import HomoSapiensScipt, TSSL, ASTScript
from core import WORKSPACE, MAPS_DIR, analyze, output
from index import get_index
from ir import Unbabel
from pathlib import Path

def to_ast(target_folder: Path):
    source_name = target_folder.stem
    objs = []
    sources = []
    for target_file in target_folder.iterdir():
        if target_file.suffix == '.txt' or target_file.suffix == '.vbs':
            sources.append(target_file)
            objs.append(analyze(target_file, TSSL))
    output_folder = WORKSPACE / 'output' / source_name
    if not output_folder.exists():
        output_folder.mkdir(parents=True)
    titles = list(map(lambda path: path.stem, sources))
    output(HomoSapiensScipt(), objs, titles, output_folder / f"{source_name}.txt", count=True)
    output(ASTScript(), objs, titles, output_folder / f"{source_name}_ast.json")

def try_to_ir(obj):
    asset_index = get_index(WORKSPACE / 'assets')
    ir_compiler = Unbabel(MAPS_DIR / 'ir.json', asset_index)
    objs = ir_compiler(objs, supress_level=0)