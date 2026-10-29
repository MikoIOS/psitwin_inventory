"""Conservative noise gate; never uses the intent router to reject legitimate questions."""
import re
import unicodedata


def intelligible_input(text):
    value = ''.join(c for c in unicodedata.normalize('NFD', text or '') if not unicodedata.combining(c)).strip().lower()
    if not re.search(r'[a-z]', value): return False
    words = re.findall(r'[a-z0-9]+', value)
    if all(re.fullmatch(r'eh+|ah+|uh+|em+|mmm+|hmm+|ruido|silencio|inaudible', w) for w in words): return False
    return not re.fullmatch(r'(?:asdf|qwerty|zxcv|aaaaa|eeee+|zzzzz)+', re.sub(r'\s', '', value))
