import click
from logzero import logger

from . import utils
from .schemas import FIELDS_TO_CLEAN_UP


class FieldCleaner:
    cleaners = None
    finalizers = None
    fields = FIELDS_TO_CLEAN_UP

    def __init__(self, replacements, finalizing, verbose=False):
        self.cleaners = {}
        self.finalizers = {}
        self.verbose = verbose

        for field, contents in replacements.items():
            logger.info(f"Compiling replacements for {field}")
            self.cleaners[field] = self.compile_cleaners(contents)

        for field, contents in finalizing.items():
            self.finalizers[field] = self.compile_finalizer(contents)

    @staticmethod
    def compile_finalizer(config):
        def finalizer(string):
            if config["capitalize"]:
                string = utils.capitalize_string(string)

            if config["strip"]:
                string = string.strip()

            return string

        return finalizer

    @staticmethod
    def compile_single_cleaner(entry):
        if isinstance(entry, str):
            return utils.simple_replace_instance(entry)

        if isinstance(entry, dict):
            return utils.regex_sub_instance(**entry)

        raise ValueError(f"Invalid replacement definition: {entry!r}")

    @staticmethod
    def compile_cleaners(entries):
        return [FieldCleaner.compile_single_cleaner(e) for e in entries]

    def iter_valid_data_fields(self, data):
        for field in self.fields:
            if field not in data:
                continue

            value = data[field]
            if value is None or len(value) == 0:
                continue

            yield field, value

    def clean(self, data):
        for field, previous in self.iter_valid_data_fields(data):
            cleaned = previous

            for cleaner in self.cleaners.get(field, []):
                cleaned = cleaner(cleaned)

            if field in self.finalizers:
                cleaned = self.finalizers[field](cleaned)

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
