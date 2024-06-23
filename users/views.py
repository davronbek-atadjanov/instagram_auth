from datetime import datetime
from rest_framework import permissions
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import ValidationError
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from shared.utility import send_email
from .models import User, NEW, CODE_VERIFIED
from .serializers import SignUpSerializer, ChangeUserInformation, ChangeUserPhotoSerializer, LoginSerializer, \
    LoginRefreshSerializer, LogoutSerializer
from rest_framework.generics import CreateAPIView, UpdateAPIView


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


class ChangeUserInformationView(UpdateAPIView):
    # Foydalanuvchi faqat autentifikatsiyadan o'tgan bo'lishi kerak
    permission_classes = [IsAuthenticated, ]

    # Ushbu viewda foydalaniladigan serializator
    serializer_class = ChangeUserInformation

    # Ushbu view faqat 'patch' va 'put' HTTP metodlarini qo'llab-quvvatlaydi
    http_method_names = ['patch', 'put']

    # Joriy foydalanuvchi obyektini olish
    def get_object(self):
        return self.request.user

    # Foydalanuvchi ma'lumotlarini yangilash
    def update(self, request, *args, **kwargs):
        super(ChangeUserInformationView, self).update(request, *args, **kwargs)

        # Yangilangan ma'lumotlarni qaytarish uchun javob yaratish
        data = {
            "success": True,
            "message": "User updated successfully",
            "auth_status": request.user.auth_status
        }
        return Response(data, status=200)

    # Foydalanuvchi ma'lumotlarini qisman yangilash
    def partial_update(self, request, *args, **kwargs):
        super(ChangeUserInformationView, self).partial_update(request, *args, **kwargs)

        # Qisman yangilangan ma'lumotlarni qaytarish uchun javob yaratish
        data = {
            "success": True,
            "message": "User updated successfully",
            "auth_status": request.user.auth_status
        }
        return Response(data, status=200)

class ChangeUserPhotoView(UpdateAPIView):
    permission_classes = [IsAuthenticated, ]

    def put(self, request, *args, **kwargs):
        serializer = ChangeUserPhotoSerializer(data=request.data)

        if serializer.is_valid():
            user = request.user
            serializer.update(user, serializer.validated_data)
            return Response({
                "message": "Rasm muvaffaqiyatli yangilandi"
            })

class LoginView(TokenObtainPairView):
    serializer_class = LoginSerializer

class LoginRefreshView(TokenObtainPairView):
    serializer_class = LoginRefreshSerializer

class LogOutView(APIView):
    serializer_class = LogoutSerializer
    permission_classes = [IsAuthenticated, ]


    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=self.request.data)
        serializer.is_valid(raise_exception=True)
        try:
            refresh_token = self.request.data['refresh']
            token = RefreshToken(refresh_token)
            token.blacklist()
            data = {
                "success": True,
                "message": "You are loggout out"
            }
            return Response(data, status=206)
        except TokenError:
            return Response(status=400)
