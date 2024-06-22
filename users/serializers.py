from shared.utility import check_email_or_other
from .models import User
from rest_framework import serializers

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