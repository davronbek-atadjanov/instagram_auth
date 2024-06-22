import re
from rest_framework.exceptions import ValidationError

email_regex = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b')

def check_email_or_other(email_data):
    if re.fullmatch(email_regex, email_data):
        email_data = "email"
    else:
        data = {
            "success": False,
            "message": "Email invalid"
        }
        raise ValidationError(data)

    return email_data