from analyzer import HomoSapiensScipt, TSSL, ASTScript
from ir import Unbabel
from sys import argv
from index import get_index
from core import WORKSPACE, MAPS_DIR, analyze, output

if __name__ == '__main__':
    if len(argv) != 2:
        print(f"Usage: {argv[0]} <target_folder>")
        exit(1)
    target_folder = WORKSPACE / 'script' / argv[1]
    if not target_folder.exists():
        raise FileNotFoundError(f"Cannot find script {argv[1]}.")
# Tokenize and analyze. Note that there are legacy parameters which are no longer used.
    objs = []
    sources = []
    for target_file in target_folder.iterdir():
        if target_file.suffix == '.txt' or target_file.suffix == '.vbs':
            sources.append(target_file)
            objs.append(analyze(target_file, TSSL))
    output_folder = WORKSPACE / 'output' / argv[1]
    if not output_folder.exists():
        output_folder.mkdir(parents=True)
# Raw script => AST
    titles = list(map(lambda path: path.stem, sources))
    output(HomoSapiensScipt(), objs, titles, output_folder / f"{argv[1]}.txt", count=True)
    output(HomoSapiensScipt(print_expression=True), objs, titles, output_folder / f"{argv[1]}_with_expressions.txt")
    output(ASTScript(), objs, titles, output_folder / f"{argv[1]}_ast.json")
# AST => IR
    index = get_index(WORKSPACE / 'assets')
    ir_compiler = Unbabel(MAPS_DIR / 'ir.json', index, target_folder)
    objs = ir_compiler(objs, sources, supress_level=0)
    
