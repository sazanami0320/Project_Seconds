def valid_word_count(meta):
    return sum(map(lambda obj: len(obj['line']), filter(lambda obj: obj['type'] == 'line', meta)))
