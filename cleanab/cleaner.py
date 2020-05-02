import re

import click
from logzero import logger


re_wordsplits = re.compile(r"([^\s]+\s)")


class FieldCleaner:
    cleaners = None
    pre_cleaners = None
    fields = set()

    def __init__(self, pre_replacements, replacements):

        self.cleaners = {}
        self.pre_cleaners = {}
        for field, contents in replacements.items():
            logger.info(f"Compiling replacements for {field}")
            self.cleaners[field] = FieldCleaner.compile(contents)
            self.fields.add(field)

        for field, contents in pre_replacements.items():
            logger.info(f"Compiling pre-replacements for {field}")
            self.pre_cleaners[field] = FieldCleaner.compile(contents)
            self.fields.add(field)

    @staticmethod
    def _replacer_instance(string, replacement=""):
        def replace(x):
            if isinstance(x, str):
                return x.replace(string, replacement)
            return x

        return replace

    @staticmethod
    def _regex_sub_instance(pattern, replacement="", casesensitive=False):
        if casesensitive:
            regex = re.compile(pattern)
        else:
            regex = re.compile(pattern, flags=re.IGNORECASE)

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
        for field in self.fields:
            if field not in data or data[field] is None:
                continue
            previous = cleaned = data[field]

            cleaners = self.cleaners.get(field, [])
            pre_cleaners = self.pre_cleaners.get(field, [])

            for cleaner in pre_cleaners:
                cleaned = cleaner(cleaned)

            # When text is all uppercase, try to capitalize it more nicely
            if cleaned.upper() == cleaned:
                cleaned = "".join(
                    s.lstrip().capitalize() for s in re_wordsplits.split(cleaned)
                )
            for cleaner in cleaners:
                cleaned = cleaner(cleaned)

            cleaned = cleaned.strip()
            # cleaned = cleaned[0].upper() + cleaned[1:]
            if previous != cleaned:
                interdot = click.style("\u00B7", fg="blue")
                previous = previous.replace(
                    " ", interdot + click.style("", fg="red", reset=False)
                )
                cleaned = cleaned.replace(
                    " ", interdot + click.style("", fg="green", reset=False)
                )
                click.echo(f"{field:>16s}" + click.style(f" - '{previous}'", fg="red"))
                click.echo(f"{'=>':>16s}" + click.style(f" + '{cleaned}'", fg="green"))

                data[field] = cleaned
        return data

    @staticmethod
    def lowercase_tld_match(pat):
        return pat.group(1) + pat.group(2).lower()
