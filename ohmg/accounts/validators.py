from django.contrib.auth.validators import UnicodeUsernameValidator


class OHMGUnicodeUsernameValidator(UnicodeUsernameValidator):
    """
    Slight change to UnicodeUsernameValidator so that it doesn't allow @.
    """

    regex = r"^[\w.+-]+\Z"
    message = "Username may contain only letters, numbers, and . + - _"


custom_username_validators = [
    OHMGUnicodeUsernameValidator(),
]
