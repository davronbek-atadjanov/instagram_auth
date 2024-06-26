from django.contrib.auth import authenticate
from django.contrib.auth.models import update_last_login
from django.contrib.auth.password_validation import validate_password
from django.core.validators import FileExtensionValidator
from rest_framework.generics import get_object_or_404
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer, TokenRefreshSerializer
from rest_framework_simplejwt.tokens import AccessToken

from shared.utility import check_email_or_other, send_email, check_input_type
from .models import User, CODE_VERIFIED, DONE, PHOTO_DONE, NEW
from rest_framework import serializers
from rest_framework.exceptions import ValidationError, PermissionDenied, NotFound


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
        # print(data)
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
                "message": "Bu email dan allaqachon foydalanilgan "
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


class ChangeUserInformation(serializers.Serializer):
    # Foydalanuvchidan kiritiladigan ma'lumotlar uchun maydonlar
    first_name = serializers.CharField(write_only=True, required=True)
    last_name = serializers.CharField(write_only=True, required=True)
    username = serializers.CharField(write_only=True, required=True)
    password = serializers.CharField(write_only=True, required=True)
    confirm_password = serializers.CharField(write_only=True, required=True)

    # Parolni va tasdiqlash parolini tekshirish uchun umumiy validate metodi
    def validate(self, data):
        password = data.get('password')
        confirm_password = data.get('confirm_password')

        # Parol va tasdiqlash paroli bir xil ekanligini tekshirish
        if password != confirm_password:
            raise ValidationError({
                "success": False,
                "message": "Parolingiz va tasqitlash parolingiz bir-biriga teng emas"
            })

        # Parolning kuchlilik talablarga javob berishini tekshirish
        if password:
            validate_password(password)
            validate_password(confirm_password)

        return data

    # Foydalanuvchi nomini tekshirish
    def validate_username(self, username):
        if len(username) < 5 or len(username) > 30:
            raise ValidationError({
                "message": "Username must be between 5 and 30 characters long"
            })
        if username.isdigit():
            raise ValidationError({
                "message": "This username is entirely numeric"
            })
        return username

    # Foydalanuvchi ismni tekshirish
    def validate_first_name(self, first_name):
        if len(first_name) < 5 or len(first_name) > 30:
            raise ValidationError({
                "message": "First_name must be between 5 and 30 characters long"
            })
        if first_name.isdigit():
            raise ValidationError({
                "message": "This first name is entirely numeric"
            })
        return first_name

    # Foydalanuvchi familiyasini tekshirish
    def validate_last_name(self, last_name):
        if len(last_name) < 5 or len(last_name) > 30:
            raise ValidationError({
                "message": "Last_name must be between 5 and 30 characters long"
            })
        if last_name.isdigit():
            raise ValidationError({
                "message": "This last name is entirely numeric"
            })
        return last_name

    # Foydalanuvchi ma'lumotlarini yangilash
    def update(self, instance, validated_data):
        # Ism, familiya, foydalanuvchi nomi va parolni yangilash
        instance.first_name = validated_data.get('first_name', instance.first_name)
        instance.last_name = validated_data.get('last_name', instance.last_name)
        instance.username = validated_data.get('username', instance.username)
        instance.password = validated_data.get('password', instance.password)

        # Agar parol yangilanayotgan bo'lsa, uni shifrlash
        if validated_data.get('password'):
            instance.set_password(validated_data.get('password'))

        # Foydalanuvchi tasdiqlangan holatiga o'zgartirilganligini belgilash
        if instance.auth_status == CODE_VERIFIED:
            instance.auth_status = DONE

        # Ma'lumotlarni saqlash
        instance.save()
        return instance

class ChangeUserPhotoSerializer(serializers.Serializer):
    photo = serializers.ImageField(validators=[FileExtensionValidator(allowed_extensions=['png', 'jpeg', 'jpg'])])

    def update(self, instance, validate_data):
        photo = validate_data.get('photo')

        if photo:
            instance.photo = photo
            instance.auth_status = PHOTO_DONE
            instance.save()
        return instance

class LoginSerializer(TokenObtainPairSerializer):

    def __init__(self, *args, **kwargs):
        super(LoginSerializer, self).__init__(*args, **kwargs)
        self.fields['user_input'] = serializers.CharField(required=True)
        self.fields['username'] = serializers.CharField(required=False, read_only=True)

    def auth_validate(self, data):
        global username
        user_input = data.get('user_input')
        if check_input_type(user_input) == "username":
            username = user_input
        elif check_input_type(user_input) == "email":
            user = self.get_user(email__iexact=user_input)
            username = user_input
        else:
            data = {
                "success": False,
                "message": "Siz username yoki email  jo'natishingiz kerak"
            }

        authentication_kwargs = {
            self.username_field: username,
            'password': data['password']
        }

        # user statusini tekshiramiz
        current_user = User.objects.filter(username__iexact=username).first()
        if current_user is not None and current_user.auth_status in [NEW, CODE_VERIFIED]:
            raise ValidationError({
                "success": False,
                "message": "Siz ro'yxatdan to'liq o'tmagansiz"
            })
        user = authenticate(**authentication_kwargs)
        if user is not None:
            self.user = user
        else:
            raise ValidationError(
                {
                    "success": False,
                    "message": "Kechirasiz, login yoki parolingiz xato,Ilimos qaytadan urinib ko'ring"
                }
            )


    def validate(self, data):
        self.auth_validate(data)
        if self.user.auth_status not in [DONE, PHOTO_DONE]:
            raise PermissionDenied("Siz login qila olmaysiz, Sizni ruxsatingiz yo'q")
        data = self.user.token()
        data['auth_status'] = self.user.auth_status
        data['fullname'] = self.user.full_name
        return data

    def get_user(self, **kwargs):
        users = User.objects.filter(**kwargs)
        if not users.exists():
            raise ValidationError({
                "message": "Bunda akkout topilmadi"
            })
        return users.first()

class LoginRefreshSerializer(TokenRefreshSerializer):

    def validate(self, attrs):
        data = super().validate(attrs)
        access_token_instance = AccessToken(data['access'])
        user_id = access_token_instance['user_id']
        user = get_object_or_404(User, id=user_id)
        update_last_login(None, user)
        return data

class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()

class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.CharField(write_only=True, required=True)

    def validate(self, attrs):
        email = attrs.get('email', None)
        if email is None:
            data = {
                "success": False,
                "messaeg": "Email xato kiritilgan, boshqata urinib ko'ring"
            }
        user = User.objects.filter(email=email)
        if not user.exists():
            raise NotFound(detail="User not found")
        attrs['user'] = user.first()
        return attrs


class ResetPasswordSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    password = serializers.CharField(min_length=8, write_only=True, required=True)
    confirm_password = serializers.CharField(min_length=8,write_only=True, required=True)

    class Meta:
        model = User
        fields = (
            'id',
            'password',
            'confirm_password'
        )

    def validate(self, data):
        password = data.get('password')
        confirm_password = data.get('confirm_password')

        if password != confirm_password:
            raise ValidationError({
                "success": False,
                "message": "Parolingiz tastiqlash parolingiz bilan bir xil emas"
            })
        if password:
            validate_password(password)
        return data

    def update(self, instance, validated_data):
        password = validated_data.pop('password')
        instance.set_password(password)
        return super(ResetPasswordSerializer, self).update(instance, validated_data)


