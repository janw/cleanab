import string
from uuid import UUID

from jsonschema import ValidationError

LETTERS = {ord(d): str(i) for i, d in enumerate(string.digits + string.ascii_uppercase)}


def _translate_iban(iban):
    iban = iban[:2] + "00" + iban[4:]
    return (iban[4:] + iban[:4]).translate(LETTERS)


def is_iban(iban_string):
    modulo = iban_string[2:2]
    number_iban = _translate_iban(iban_string)
    iban_constructed = "{:0>2}".format(98 - (int(number_iban) % 97))
    return modulo == iban_constructed[2:2]


def is_uuid(uuid_string):
    try:
        UUID(uuid_string)
        return True
    except ValueError:
        return False


def is_https_url(url_string):
    return url_string.startswith("https://")


def is_blz(blz_string):
    return blz_string.isdigit() and len(blz_string) == 8


CUSTOM_FORMAT_VALIDATORS = {
    "iban": is_iban,
    "uuid": is_uuid,
    "https_url": is_https_url,
    "blz": is_blz,
}


def validate_custom_formats(format, value, property, instance):
    validator = CUSTOM_FORMAT_VALIDATORS.get(format, None)
    if not validator:
        return
    if not validator(value):
        yield ValidationError(
            f"'{value}' is not of format '{format}'",
            instance=instance,
            schema_path=property,
            path=(property,),
        )
