import uuid
import random
from datetime import datetime, timedelta

from django.contrib.auth.models import AbstractUser
from django.core.validators import FileExtensionValidator
from django.db import models
from rest_framework_simplejwt.tokens import RefreshToken

from shared.models import BaseModel

NEW, CODE_VERIFIED, DONE, PHOTO_DONE = ('new', 'code_verified', 'done', 'photo_done')
ORDINARY_USER, MANAGER, ADMIN = ('ordinary_user', 'manager', 'admin')


class User(AbstractUser, BaseModel):
    AUTH_STATUS = (
        (NEW, NEW),
        (CODE_VERIFIED, CODE_VERIFIED),
        (DONE, DONE),
        (PHOTO_DONE, PHOTO_DONE)
    )

    USER_ROLES = (
        (ORDINARY_USER, ORDINARY_USER),
        (MANAGER, MANAGER),
        (ADMIN, ADMIN)
    )

    user_roles = models.CharField(max_length=31, choices=USER_ROLES, default=ORDINARY_USER)
    auth_status = models.CharField(max_length=31, choices=AUTH_STATUS, default=NEW)
    email = models.EmailField(null=False, blank=False, unique=True)
    photo = models.ImageField(upload_to='user_photos/', null=True, blank=True,
                              validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png'])])

    def __str__(self):
        return self.username

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def create_verify_code(self):
        code = "".join([str(random.randint(1, 100) % 10) for _ in range(4)])
        UserConfirmation.objects.create(
            user_id=self.id,
            code=code
        )
        return code

    def check_username(self):
        # username maydoni bo'shligini tekshirish
        if not self.username:
            # UUID yordamida vaqtinchalik username yaratish
            temp_username = f"instagram-{uuid.uuid4().__str__().split('-')[-1]}"
            # Yaratilgan username noyob ekanligini ta'minlash
            while User.objects.filter(username=temp_username).exists():
                temp_username = f"{temp_username}{random.randint(0, 9)}"
            # Noyob vaqtinchalik username ni username maydoniga o'rnatish
            self.username = temp_username

    def check_email(self):
        # Agar email manzili mavjud bo'lsa
        if self.email:
            # Email manzilini kichik harflarda yozish
            normalize_email = self.email.lower()
            # Kichik harflarda yozilgan email manzilini email maydoniga o'rnatish
            self.email = normalize_email

    def check_pass(self):
        # password maydoni bo'shligini tekshirish
        if not self.password:
            # UUID yordamida vaqtinchalik parol yaratish
            temp_password = f"password-{uuid.uuid4().__str__().split('-')[-1]}"
            # Vaqtinchalik parolni password maydoniga o'rnatish
            self.password = temp_password

    def hashing_password(self):
        # password maydoni pbkdf2_sha256 bilan boshlanmasligini tekshirish
        if not self.password.startswith('pbkdf2_sha256'):
            # Parolni xesh qilish uchun self.set_password metodidan foydalanish
            self.set_password(self.password)

    def token(self):
        # Foydalanuvchi uchun yangilanish tokenini yaratish
        refresh = RefreshToken.for_user(self)
        return {
            # Yangilanish tokenidan foydalanib kirish tokenini olish
            "access": str(refresh.access_token),
            # Yangilanish tokenini olish
            "refresh_token": str(refresh)
        }

    def save(self, *args, **kwargs):
        # Email manzilini tekshirish
        self.check_email()
        # Username maydoni bo'sh bo'lsa, vaqtinchalik noyob username yaratish
        self.check_username()
        # Parol maydoni bo'sh bo'lsa, vaqtinchalik parol yaratish
        self.check_pass()
        # Parol allaqachon xeshlanmagan bo'lsa, parolni xeshlash
        self.hashing_password()
        # Super klassning save metodini chaqirish va o'zgarishlarni saqlash
        super(User, self).save(*args, **kwargs)


EMAIL_EXPIRE = 5  # Tasdiqlash kodining amal qilish muddati (daqiqa hisobida)


class UserConfirmation(BaseModel):
    code = models.CharField(max_length=4)  # 4 raqamli kod uchun maydon
    user = models.ForeignKey('users.User', models.CASCADE, related_name='verify_codes')  # User modeliga foreign key
    expiration_time = models.DateTimeField(null=True)  # Kodning tugash vaqti
    is_confirmed = models.BooleanField(default=False)  # Kod tasdiqlanganligini belgilovchi flag

    def __str__(self):
        return str(self.user.__str__())

    def save(self, *args, **kwargs):
        # Tasdiqlash kodining amal qilish muddatini hozirgi vaqtdan EMAIL_EXPIRE daqiqa keyin o‘rnatish
        self.expiration_time = datetime.now() + timedelta(minutes=EMAIL_EXPIRE)
        super(UserConfirmation, self).save(*args, **kwargs)
