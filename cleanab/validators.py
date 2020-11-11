import string
from uuid import UUID

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
