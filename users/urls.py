from django.urls import path, include
from .views import CreateUserView, VerifyApiView, GetNewVerificationView, ChangeUserInformationView

urlpatterns = [
    path('signup/', CreateUserView.as_view()),
    path('verify/', VerifyApiView.as_view()),
    path('new-verify/',GetNewVerificationView.as_view()),
    path('change-user/', ChangeUserInformationView.as_view()),
]