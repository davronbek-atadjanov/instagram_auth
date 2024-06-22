
from shared.utility import check_email_or_other, send_email
from .models import User
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
class SignUpSerializer(serializers.ModelSerializer):
    # Foydalanuvchi identifikatori uchun faqat o'qish mumkin bo'lgan UUID maydoni
    id = serializers.UUIDField(read_only=True)
    # Avtorizatsiya holati uchun faqat o'qish mumkin bo'lgan maydon, kerak emas
    auth_status = serializers.CharField(read_only=True, required=False)

    def __init__(self, *args, **kwargs):
        # Ota klassni boshlash
        super(SignUpSerializer, self).__init__(*args, **kwargs)
        # 'email' maydonini dinamik ravishda qo'shish va uni kerak emas deb belgilash
        self.fields['email'] = serializers.CharField(required=False)

    class Meta:
        # Ishlatiladigan modelni ko'rsatish
        model = User
        # Seriyalangan chiqishda kiritiladigan maydonlarni ko'rsatish
        fields = (
            'id',
            'auth_status'
        )

    def create(self, validated_data):
        # `super` yordamida ota klassning `create` metodini chaqirib, foydalanuvchini yaratadi.
        user = super(SignUpSerializer, self).create(validated_data)
        # Yangi yaratilgan foydalanuvchi uchun verifikatsiya kodini yaratadi.
        code = user.create_verify_code()
        # Verifikatsiya kodini foydalanuvchining elektron pochta manziliga yuboradi.
        send_email(user.email, code)
        # Foydalanuvchini saqlaydi.
        user.save()
        # Yaratilgan foydalanuvchini qaytaradi.
        return user

    def validate(self, data):
        # Ota klassning validate metodini chaqirish
        super(SignUpSerializer, self).validate(data)
        # Maxsus tasdiqlashni bajarish va tasdiqlangan ma'lumotlarni qaytarish
        data = self.auth_validate(data)
        return data

    @staticmethod
    def auth_validate(data):
        # Kiruvchi ma'lumotlarni tekshirish uchun chop etish
        print(data)
        # Foydalanuvchi kiritgan ma'lumotlarni kichik harflarga o'zgartirish
        user_input = str(data.get('email')).lower()

        # Agar kiritilgan ma'lumot email bo'lsa, uni qaytarish
        if check_email_or_other(user_input) == "email":
            data = {
                "email": user_input
            }
        else:
            # Agar email bo'lmasa, xato xabarini qaytarish
            data = {
                "success": False,
                "message": "Siz email yuborishingiz kerak"
            }
        return data

    def validate_email(self, value):
        # Email manzilini kichik harflarga o'zgartiradi.
        value = value.lower()
        # Agar berilgan email manzili bo'sh bo'lmasa va User modelida mavjud bo'lsa:
        if value and User.objects.filter(email=value).exists():
            # Xato xabari uchun ma'lumotlar tayyorlanadi.
            data = {
                "success": False,
                "message": "Bu email dan allaqachon fodalanilgan "
                # O'zbek tilida "Bu email allaqachon foydalanilgan" deb yozilgan.
            }
            # ValidationError chiqariladi va ma'lumotlar unga qo'shiladi.
            raise ValidationError(data)
        # Agar email mavjud bo'lmasa, uni qaytaradi.
        return value

    def to_representation(self, instance):
        # Super klassning to_representation metodini chaqirib, instance ma'lumotlarini olish
        data = super(SignUpSerializer, self).to_representation(instance)
        # instance.token() metodidan foydalanib, foydalanuvchi uchun yangilanish tokenlarini olish
        token_data = instance.token()
        # data o'zgaruvchisiga yangilanish tokenlarni qo'shib qo'yish
        data.update(token_data)
        # Tuzilgan ma'lumotlarni qaytarish
        return data
