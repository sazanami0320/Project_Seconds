from pathlib import Path
from analyzer import TSSL, ASTScript
from utils import valid_word_count
import json

WORKSPACE = Path(__file__).resolve().parent.parent
MAPS_DIR = WORKSPACE / 'src' / 'maps'

def analyze(target_file: Path, base_class):
    if base_class is TSSL:
        with open(MAPS_DIR / 'tssl.json', 'r', encoding='utf-8') as f:
            tssl_config = json.load(f)
        instance = TSSL(tssl_config)
    else:
        instance = base_class()
    
    try:
        with target_file.open('r', encoding='utf-8') as f:
            obj = instance.encode(f.read(), filename=target_file.stem)
    except UnicodeEncodeError as e:
        with target_file.open('r', encoding='gb2312') as f:
            obj = instance[base_class].encode(f.read())
    except Exception as e:
        if base_class is TSSL:
            print(f"At line {instance.lineno} of file {target_file.stem}:")
        raise e from None
    return obj

def output(instance, objs, titles, targe_file, *args, count=False, **kwargs):
    json_flag = isinstance(instance, ASTScript)
    with targe_file.open('w', encoding='utf-8') as f:
        if json_flag:
            f.write('[\n')
        for index, (title, meta_obj) in enumerate(zip(titles, objs)):
            if count:
                word_count = valid_word_count(meta_obj)
                print(f"{title}: {word_count} characters processed.")
            f.write(instance.decode(meta_obj, *args, **kwargs))
            if json_flag and index < len(objs) - 1:
                f.write(',\n')
        if json_flag:
            f.write(']\n')
