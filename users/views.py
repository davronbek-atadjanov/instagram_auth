from datetime import datetime
from rest_framework import permissions
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import ValidationError

from shared.utility import send_email
from .models import User, NEW, CODE_VERIFIED
from .serializers import SignUpSerializer
from rest_framework.generics import CreateAPIView


class CreateUserView(CreateAPIView):
    queryset = User.objects.all()
    permission_classes = [permissions.AllowAny]
    serializer_class = SignUpSerializer


class VerifyApiView(APIView):
    # Foydalanuvchi autentifikatsiyadan o'tganligini tekshirish uchun ruxsat beruvchi sinf
    permission_classes = [IsAuthenticated, ]

    def post(self, request, *args, **kwargs):
        # Foydalanuvchi obyektini olish (foydalanuvchi autentifikatsiyadan o'tgan bo'lishi kerak)
        user = self.request.user
        # Foydalanuvchi yuborgan tasdiqlash kodini olish
        code = self.request.data.get('code')
        # Tasdiqlash kodini tekshirish
        self.check_verify(user, code)
        # Tasdiqlash muvaffaqiyatli bo'lsa, javobni qaytarish
        return Response(
            {
                "success": True,
                "auth_status": user.auth_status,
                # Foydalanuvchiga kirish va yangilanish tokenlarini qaytarish
                "access": user.token()['access'],
                "refresh": user.token()['refresh_token']
            }
        )

    @staticmethod
    def check_verify(user, code):
        # Foydalanuvchi tomonidan yuborilgan kodning amal qilish muddati va tasdiqlanganligini tekshirish
        verifies = user.verify_codes.filter(expiration_time__gte=datetime.now(), code=code, is_confirmed=False)

        # Agar bunday tasdiqlash kodi mavjud bo'lmasa
        if not verifies.exists():
            data = {
                "message": "Tasdiqlash kodingiz xato yoki eskirgan"
            }
            # Xatolikni qaytarish
            raise ValidationError(data)
        else:
            # Agar kod to'g'ri bo'lsa, tasdiqlanganligini yangilash
            verifies.update(is_confirmed=True)

        # Agar foydalanuvchining autentifikatsiya holati 'NEW' bo'lsa
        if user.auth_status == NEW:
            # Autentifikatsiya holatini 'CODE_VERIFIED' ga o'zgartirish
            user.auth_status = CODE_VERIFIED
            # O'zgarishlarni saqlash
            user.save()
        # Va True qaytaramiz
        return True


class GetNewVerificationView(APIView):
    # Foydalanuvchi autentifikatsiyadan o'tganligini tekshirish uchun ruxsat beruvchi sinf
    permission_classes = [IsAuthenticated, ]

    def get(self, request, *args, **kwargs):
        # Foydalanuvchi obyektini olish (foydalanuvchi autentifikatsiyadan o'tgan bo'lishi kerak)
        user = self.request.user
        # Foydalanuvchining tasdiqlash kodini tekshirish
        self.check_verification(user)
        # Foydalanuvchi uchun yangi tasdiqlash kodini yaratish
        code = user.create_verify_code()
        # Yangi tasdiqlash kodini foydalanuvchiga elektron pochta orqali yuborish
        send_email(user, code)
        # Muvaffaqiyatli javobni qaytarish
        return Response(
            {
                "success": True,
                "message": "Tasdiqlash kodingiz qayta yuborildi"
            }
        )

    @staticmethod
    def check_verification(user):
        # Foydalanuvchi tomonidan yaratilgan va hali eskirmagan, tasdiqlanmagan tasdiqlash kodlarini olish
        verifies = user.verify_codes.filter(expiration_time__gte=datetime.now(), is_confirmed=False)

        # Agar bunday tasdiqlash kodlari mavjud bo'lsa
        if verifies.exists():
            data = {
                "message": "Kodingiz hali ishlatish uchun yaroqli, birozdan keyin urinib ko'ring"
            }
            # Xatolikni qaytarish (foydalanuvchi hali yangi kod so'rov qilishiga ruxsat berilmaydi)
            raise ValidationError(data)
