from pathlib import Path
from typing import Dict, List, Optional
import pickle
import re

PIC_SUFFIXES = ['png', 'jpg', 'jpeg', 'bmp', 'raw']
AUDIO_SUFFIXES = ['ogg', 'mp3', 'wav', 'flac']

# I'm pretty sure this would not be used
def deep_merge_dict(target_dict: dict, new_dict: dict):
    if not isinstance(new_dict, dict):
        raise RuntimeError(f"Bad hierarchy structure at {new_dict}.")
    for key, value in new_dict.items():
        if key in target_dict:
            deep_merge_dict(target_dict[key], value)
        else:
            target_dict[key] = value


def index_simple_dir(folder: Path, accept_suffixes: Optional[List[str]]=None) -> Dict[str, Dict | Path]:
    if folder.is_file():
        raise RuntimeError(f"Expect {folder} to be a directory, turns out to be a file.")
    result = {}
    for item in folder.iterdir():
        if item.is_file():
            if accept_suffixes is None or item.suffix[1:] in accept_suffixes:
                result[item.stem] = item
        else:
            result[item.stem] = index_simple_dir(item)
    return result


def index_hierarchy(hierarchical_dir: Path, accept_suffixes: Optional[List[str]]=None, max_level: int=1) -> Dict[str, Dict]:
    result = {}
    for h_item in hierarchical_dir.iterdir():
        if h_item.is_dir():
            sub_result = index_simple_dir(result, accept_suffixes)
            if h_item.stem in result:
                old_value = result[h_item.stem]
                if not isinstance(old_value, dict):
                    raise RuntimeError(f"{h_item} is a directory yet already covered by file")
                deep_merge_dict(old_value, sub_result)
            else:
                result[h_item.stem] = sub_result
        else:
            if accept_suffixes is not None and h_item.suffix[1:] not in accept_suffixes:
                continue
            file_name_parts = h_item.stem.split('_')
            index_level = min(len(file_name_parts) - 1, max_level)
            keys = file_name_parts[:index_level]
            name = '_'.join(file_name_parts[index_level:])
            current = result
            for key in keys:
                if key in current:
                    current = current[key]
                else:
                    _temp = {}
                    current[key] = _temp
                    current = _temp
            current[name] = h_item
    return result

def update_index(asset_dir: Path, art_dir_name: Optional[str]):
    index = {}
    if art_dir_name is None:
        art_dir = asset_dir
    else:
        art_dir = asset_dir / art_dir_name
    index['bg'] = index_hierarchy(art_dir / 'bg', PIC_SUFFIXES)
    index['cg'] = index_hierarchy(art_dir / 'cg', PIC_SUFFIXES)
    index['fg'] = index_hierarchy(art_dir / 'fg', PIC_SUFFIXES)
    index['se'] = index_simple_dir(art_dir / 'se', AUDIO_SUFFIXES)
    # Deal with stance of fg specially
    chara_pattern = re.compile(r'([a-zA-z]+)(\d+)')
    new_fg_dict = {}
    for key, value in index['fg'].items():
        match_object = chara_pattern.fullmatch(key)
        if match_object is None:
            new_fg_dict[key] = value
        else:
            chara_name, stance = match_object.groups()
            if chara_name not in new_fg_dict:
                new_fg_dict[chara_name] = {}
            # list the same expression with different stance
            # This section of code can be vulnerable to asset directory structure
            for expression, path in value.items():
                if expression in new_fg_dict[chara_name]:
                    new_fg_dict[chara_name][expression].append(path)
                else:
                    new_fg_dict[chara_name][expression] = [path]
    index['fg'] = new_fg_dict
    with open(asset_dir / 'index.pickle', 'wb') as f:
        pickle.dump(index, f)
    return index

def get_index(asset_dir:Path, art_dir_name: Optional[str]='游戏资产'):
    update_flag = False
    index_file = asset_dir / 'index.pickle'
    if index_file.exists():
        update_flag = index_file.stat().st_mtime < asset_dir.stat().st_mtime
    else:
        update_flag = True
    if update_flag:
        print('Updating asset index...')
        return update_index(asset_dir, art_dir_name)
    else:
        with index_file.open('rb') as f:
            return pickle.load(f)
