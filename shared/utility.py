import re
import threading

from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from rest_framework.exceptions import ValidationError

email_regex = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b')
username_regex = re.compile(r"^[a-zA-z0-9_.-]+$")
def check_email_or_other(email_data):
    """
    Tekshiriladigan ma'lumotning email formatiga mos kelishini tekshirish uchun funksiya.
    Args:
        email_data (str): Tekshiriladigan email ma'lumoti.
    Returns:
        str: "email" deb qaytariladi, agar email formatiga mos kelgan bo'lsa.
    Raises:
        ValidationError: Agar berilgan ma'lumot email formatiga mos kelmasa.
    """
    if re.fullmatch(email_regex, email_data):
        email_data = "email"
    else:
        data = {
            "success": False,
            "message": "Email invalid"
        }
        raise ValidationError(data)

    return email_data
class EmailThread(threading.Thread):
    """
    Asinxron rejimda emailni jo'natish uchun threading.Thread dan meros olgan klass.
    """
    def __init__(self, email):
        """
        EmailThread obyektini yaratish uchun email obyektini qabul qiladi.
        Args:
            email (EmailMessage): Jo'natiladigan email obyekti.
        """
        self.email = email
        threading.Thread.__init__(self)

    def run(self):
        """
        Threadning ishga tushirilishi.
        Emailni jo'natish operatsiyasini boshlash uchun email obyektini jo'natadi.
        """
        self.email.send()

class Email:
    """
    Email jo'natish uchun yordamchi klass.
    """
    @staticmethod
    def send_email(data):
        """
        Emailni yuborish uchun EmailMessage obyektini yaratadi va unga asinxron rejimda
        jo'natish uchun EmailThread obyektini yaratib ishga tushiradi.
        Args:
            data (dict): Email jo'natish ma'lumotlari (subject, body, to_email, content_type).
        """
        email = EmailMessage(
            subject=data['subject'],
            body=data['body'],
            to=[data['to_email']]
        )
        if data.get('content_type') == "html":
            email.content_subtype = 'html',
        EmailThread(email).start()

def send_email(email, code):
    """
    Berilgan emailga aktivatsiya kodi bilan ro'yxatdan o'tish xabarnomasini yuborish funktsiyasi.
    Args:
        email (str): Foydalanuvchi email manzili.
        code (str): Ro'yxatdan o'tish kodi.
    """
    html_content = render_to_string(
        'email/authentication/activate_account.html',
        {"code": code}
    )
    Email.send_email(
        {
            "subject": "Ro'yxatdan o'tish",
            "to_email": email,
            "body": html_content,
            "content_type": "html"
        }
    )

def check_input_type(user_input):
    if re.fullmatch(email_regex, user_input):
        user_input = "email"
    elif re.fullmatch(username_regex, user_input):
        user_input = "username"
    else:
        data = {
            "success": False,
            "message": "Username yoki email noto'g'ri kiritilgan"
        }
        raise ValidationError(data)
    return user_input
