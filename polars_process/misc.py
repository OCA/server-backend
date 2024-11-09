def slug_me(string, except_pattern_list=None):
    if not except_pattern_list:
        except_pattern_list = []
    for pattern, subst in {" ": "-", "'": "", '"': "", "/": "-", ".": "-"}.items():
        if pattern not in except_pattern_list:
            string = string.replace(pattern, subst).lower()
    return string
