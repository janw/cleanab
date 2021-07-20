import re

re_wordsplits = re.compile(r"([^\s\-]+(\s|$))")


def _replace_capitalize(match):
    return match.group(1).capitalize()


def capitalize_string(string):
    return re_wordsplits.sub(_replace_capitalize, string)


def simple_replace_instance(string, replacement=""):
    def replace(x):
        return x.replace(string, replacement)

    return replace


def regex_sub_instance(*, pattern, repl="", caseinsensitive=True):
    regex = re.compile(
        pattern,
        flags=re.IGNORECASE if caseinsensitive else 0,
    )

    def substitute(x):
        return regex.sub(repl, x)

    return substitute
