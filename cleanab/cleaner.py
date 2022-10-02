import re

from logzero import logger

from . import utils
from .constants import FIELDS_TO_CLEAN_UP
from .models.cleaner import ReplacementDefinition


class FieldCleaner:
    cleaners = None
    finalizers = None
    fields = FIELDS_TO_CLEAN_UP

    def __init__(self, replacements, finalizing):
        self.cleaners = {}
        self.finalizers = {}

        for field, contents in replacements:
            logger.info(f"Compiling replacements for {field}")
            self.cleaners[field] = self.compile_cleaners(contents)

        for field, contents in finalizing:
            self.finalizers[field] = self.compile_finalizer(contents)

    @staticmethod
    def compile_finalizer(config):
        def finalizer(string):
            if config.capitalize:
                string = utils.capitalize_string(string)

            if config.strip:
                string = string.strip()

            return string

        return finalizer

    @staticmethod
    def compile_single_cleaner(entry):
        if isinstance(entry, str):
            return utils.simple_replace_instance(entry)

        if isinstance(entry, ReplacementDefinition):
            return entry.get_cleaner()

        raise ValueError(f"Invalid replacement definition: {entry!r}")

    @staticmethod
    def compile_cleaners(entries):
        cleaners = []
        for entry in entries:
            if isinstance(entry, list):
                cleaners += FieldCleaner.compile_cleaners(entry)
            else:
                cleaners.append(FieldCleaner.compile_single_cleaner(entry))
        return cleaners

    def iter_valid_data_fields(self, data):
        for field in self.fields:
            if field not in data:
                continue

            value = data[field]
            if value is None or len(value) == 0:
                continue

            yield field, value

    def clean_field(self, field, cleaned):
        transformations = {}
        for cleaner in self.cleaners.get(field, []):
            before_cleaning = cleaned
            cleaned, local_transformations = cleaner(cleaned)
            if before_cleaning != cleaned:
                logger.debug(f"Cleaned '{before_cleaning}' => '{cleaned}'")
            transformations.update(local_transformations)

        return cleaned, transformations

    def clean(self, data):
        transformations = {}
        try:
            for field, previous in self.iter_valid_data_fields(data):
                cleaned, local_transformations = self.clean_field(field, previous)
                transformations.update(local_transformations)
                data[field] = cleaned

            for field, transformation in transformations.items():
                data[field] = transformation

            for field, previous in self.iter_valid_data_fields(data):
                if field in self.finalizers:
                    data[field] = self.finalizers[field](previous)
        except re.error as exc:
            raise ValueError(f"Exception for pattern {exc.pattern}") from exc

        return data
