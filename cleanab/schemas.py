from copy import deepcopy

from dateutil.parser import parse as dateparse
from jsonschema import draft7_format_checker
from jsonschema import Draft7Validator
from jsonschema import validators

from .types import AccountType
from .validators import validate_custom_formats

ACCOUNT_CONFIG_SCHEMA = {
    "type": "object",
    "properties": {
        "iban": {
            "type": "string",
            "format": "iban",
        },
        "ynab_id": {
            "type": "string",
            "format": "uuid",
        },
        "fints_username": {
            "type": "string",
        },
        "fints_password": {
            "type": "string",
        },
        "fints_blz": {
            "type": "string",
            "format": "blz",
        },
        "fints_endpoint": {
            "type": "string",
            "format": "https_url",
        },
        "friendly_name": {
            "type": "string",
        },
        "account_type": {
            "type": "string",
            "enum": AccountType.choices(),
            "default": AccountType.CHECKING.value,
        },
        "default_cleared": {
            "type": "boolean",
            "default": False,
        },
        "default_approved": {
            "type": "boolean",
            "default": False,
        },
    },
}

TIMESPAN_CONFIG_SCHEMA = {
    "type": "object",
    "properties": {
        "earliest_date": {
            "type": "string",
            "format": "date",
            "default": "2000-01-01",
        },
        "maximum_days": {
            "type": "integer",
            "minimum": 1,
            "default": 30,
        },
    },
    "required": [],
}

YNAB_CONFIG_SCHEMA = {
    "type": "object",
    "properties": {
        "access_token": {
            "type": "string",
        },
        "budget_id": {
            "type": "string",
            "format": "uuid",
        },
        "cash_account_id": {
            "type": "string",
            "format": "uuid",
        },
    },
    "required": ["access_token", "budget_id"],
}

_REPLACEMENT_SUBDEFINITION = {
    "oneOf": [
        {
            "type": "string",
        },
        {
            "type": "object",
            "properties": {
                "pattern": {
                    "type": "string",
                },
                "repl": {
                    "type": "string",
                    "default": "",
                },
                "caseinsensitive": {
                    "type": "boolean",
                    "default": True,
                },
            },
            "required": ["pattern"],
            "additionalProperties": False,
        },
    ]
}

REPLACEMENT_DEFINITION = deepcopy(_REPLACEMENT_SUBDEFINITION)
REPLACEMENT_DEFINITION["oneOf"].append(
    {
        "type": "array",
        "items": _REPLACEMENT_SUBDEFINITION,
        "default": [],
    }
)


FINALIZER_DEFINITION = {
    "type": "object",
    "properties": {
        "capitalize": {
            "type": "boolean",
            "default": True,
        },
        "strip": {
            "type": "boolean",
            "default": True,
        },
    },
    "default": {},
    "additionalProperties": False,
}

CLEANAB_CONFIG_SCHEMA = {
    "type": "object",
    "properties": {
        "concurrency": {
            "type": "integer",
            "minimum": 1,
            "default": 1,
        }
    },
}


FIELDS_TO_CLEAN_UP = ["applicant_name", "purpose"]

REPLACEMENT_FIELDS = {
    field: {
        "type": "array",
        "items": REPLACEMENT_DEFINITION,
        "default": [],
    }
    for field in FIELDS_TO_CLEAN_UP
}

FINALIZER_FIELDS = {field: FINALIZER_DEFINITION for field in FIELDS_TO_CLEAN_UP}

CONFIG = {
    "type": "object",
    "properties": {
        "cleanab": CLEANAB_CONFIG_SCHEMA,
        "timespan": TIMESPAN_CONFIG_SCHEMA,
        "ynab": YNAB_CONFIG_SCHEMA,
        "accounts": {
            "type": "array",
            "items": ACCOUNT_CONFIG_SCHEMA,
        },
        "replacements": {
            "type": "object",
            "properties": REPLACEMENT_FIELDS,
        },
        "pre-replacements": {
            "type": "object",
            "properties": REPLACEMENT_FIELDS,
        },
        "finalizer": {
            "type": "object",
            "properties": FINALIZER_FIELDS,
            "default": {field: {} for field in FIELDS_TO_CLEAN_UP},
        },
    },
    "patternProperties": {"x-.*": {}},
    "additionalProperties": False,
    "required": ["accounts", "ynab"],
}


def extend_with_default(validator_class):
    validate_properties = validator_class.VALIDATORS["properties"]

    def set_defaults(validator, properties, instance, schema):
        for property, subschema in properties.items():
            if "default" in subschema and isinstance(instance, dict):
                instance.setdefault(property, subschema["default"])

            if "format" not in subschema:
                continue

            format = subschema["format"]
            value = instance[property]

            yield from validate_custom_formats(
                format,
                value,
                property,
                instance,
            )

            if format == "date":
                instance[f"${property}__native"] = dateparse(value).date()

        yield from validate_properties(
            validator,
            properties,
            instance,
            schema,
        )

    return validators.extend(
        validator_class,
        {"properties": set_defaults},
    )


assert Draft7Validator.check_schema(CONFIG) is None

DefaultValidatingDraft7Validator = extend_with_default(Draft7Validator)

config_validator = DefaultValidatingDraft7Validator(
    schema=CONFIG,
    format_checker=draft7_format_checker,
)
