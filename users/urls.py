from django.urls import path, include
from .views import CreateUserView
urlpatterns = [
    path('signup/', CreateUserView.as_view())
]