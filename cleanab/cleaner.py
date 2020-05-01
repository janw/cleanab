import re

from logzero import logger


class FieldCleaner:
    def __init__(self, replacements):

        self.cleaners = {}
        for field, contents in replacements.items():
            logger.info(f"Compiling cleaners for {field}")
            self.cleaners[field] = FieldCleaner.compile(contents)

    @staticmethod
    def _replacer_instance(string, replacement=""):
        logger.debug(f"Compiling replacement for '{string}' => '{replacement}'")

        def replace(x):
            if isinstance(x, str):
                return x.replace(string, replacement)
            return x

        return replace

    @staticmethod
    def _regex_sub_instance(pattern, replacement="", casesensitive=False):
        logger.debug(f"Compiling regex for '{pattern}' => '{replacement}'")
        regex = re.compile(pattern, flags=re.IGNORECASE)

        if casesensitive:
            regex = re.compile(pattern)

        def substitute(x):
            if isinstance(x, str):
                return regex.sub(replacement, x)
            return x

        return substitute

    @staticmethod
    def compile(field):
        cleaners = []
        for entry in field:
            if isinstance(entry, str):
                cleaners.append(FieldCleaner._replacer_instance(entry))
            elif isinstance(entry, dict):
                subst = entry.get("repl", "")
                if "string" in entry:
                    cleaners.append(
                        FieldCleaner._replacer_instance(entry["string"], subst)
                    )

                elif "pattern" in entry:
                    casesensitive = entry.get("casesensitive", False)
                    cleaners.append(
                        FieldCleaner._regex_sub_instance(
                            entry["pattern"], subst, casesensitive
                        )
                    )
                else:
                    raise ValueError(f"Missing keyword in definition: {entry}")
            else:
                raise ValueError(f"Replacement definition must be str or dict: {entry}")
        return cleaners

    def clean(self, data):
        for field, cleaners in self.cleaners.items():
            if field in data and data[field] is not None:
                data[field] = data[field].title()
                previous = data[field]
                for cleaner in cleaners:
                    data[field] = cleaner(data[field])

                data[field] = data[field].strip()
                if previous != data[field]:
                    logger.debug(f"Cleaned {field} '{previous}' => '{data[field]}'")

        return data

    @staticmethod
    def lowercase_tld_match(pat):
        return pat.group(1) + pat.group(2).lower()
