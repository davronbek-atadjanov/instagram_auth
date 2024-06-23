from django.urls import path, include
from .views import CreateUserView, VerifyApiView, GetNewVerificationView, ChangeUserInformationView, \
    ChangeUserPhotoView, LoginView, LoginRefreshView, LogOutView

urlpatterns = [
    path('login/', LoginView.as_view()),
    path('login/refresh/', LoginRefreshView.as_view()),
    path('logout/', LogOutView.as_view()),
    path('signup/', CreateUserView.as_view()),
    path('verify/', VerifyApiView.as_view()),
    path('new-verify/',GetNewVerificationView.as_view()),
    path('change-user/', ChangeUserInformationView.as_view()),
    path('change-user-photo/', ChangeUserPhotoView.as_view()),
]