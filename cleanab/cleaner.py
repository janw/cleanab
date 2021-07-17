import re

import click
from logzero import logger


re_wordsplits = re.compile(r"([^\s\-]+(\s|$))")


class FieldCleaner:
    cleaners = None
    pre_cleaners = None
    fields = set()

    def __init__(self, pre_replacements, replacements, finalizer, verbose=False):

        self.cleaners = {}
        self.pre_cleaners = {}
        self.verbose = verbose
        self.finalizer = finalizer

        for field, contents in replacements.items():
            logger.info(f"Compiling replacements for {field}")
            self.cleaners[field] = self.compile(contents)
            self.fields.add(field)

        for field, contents in pre_replacements.items():
            logger.info(f"Compiling pre-replacements for {field}")
            self.pre_cleaners[field] = self.compile(contents)
            self.fields.add(field)

    @staticmethod
    def _replacer_instance(string, replacement=""):
        def replace(x):
            return x.replace(string, replacement)

        return replace

    @staticmethod
    def _regex_sub_instance(*, pattern, repl="", casesensitive=False):
        regex = re.compile(
            pattern,
            flags=re.IGNORECASE if casesensitive else 0,
        )

        def substitute(x):
            return regex.sub(repl, x)

        return substitute

    @staticmethod
    def compile_entry(entry):
        if isinstance(entry, str):
            return FieldCleaner._replacer_instance(entry)

        if isinstance(entry, dict):
            return FieldCleaner._regex_sub_instance(**entry)

        raise ValueError(f"Invalid replacement definition: {entry!r}")

    @staticmethod
    def compile(field):
        return [FieldCleaner.compile_entry(e) for e in field]

    def iter_field_data(self, data):
        for field in self.fields:
            if field not in data:
                continue

            previous = data[field]
            if previous is None or len(previous) == 0:
                continue

            cleaners = self.cleaners.get(field, [])
            pre_cleaners = self.pre_cleaners.get(field, [])
            finalizer = self.finalizer.get(field, [])

            yield field, previous, cleaners, pre_cleaners, finalizer

    @staticmethod
    def _replace_capitalize(match):
        return match.group(1).capitalize()

    def clean(self, data):
        for field, previous, cleaners, pre_cleaners, finalizer in self.iter_field_data(
            data
        ):
            cleaned = previous

            for cleaner in pre_cleaners:
                cleaned = cleaner(cleaned)

            if finalizer["capitalize"]:
                cleaned = re_wordsplits.sub(FieldCleaner._replace_capitalize, cleaned)

            for cleaner in cleaners:
                cleaned = cleaner(cleaned)

            if finalizer["strip"]:
                cleaned = cleaned.strip()
            data[field] = cleaned

            self._echo_if_cleaned(field, previous, cleaned)
        return data

    def _echo_if_cleaned(self, field, previous, cleaned):
        if self.verbose and previous != cleaned:
            interdot = click.style("\u00B7", fg="blue")
            previous = previous.replace(
                " ", interdot + click.style("", fg="red", reset=False)
            )
            colored = cleaned.replace(
                " ", interdot + click.style("", fg="green", reset=False)
            )
            click.echo(f"{field:>16s}" + click.style(f" - '{previous}'", fg="red"))
            click.echo(f"{'=>':>16s}" + click.style(f" + '{colored}'", fg="green"))
