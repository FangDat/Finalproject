# backend/myproject/urls.py
from django.contrib import admin
from django.urls import path
from backend.api import views
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path('admin/', admin.site.urls),

    # Auth (custom APIs)
    path('api/signup/', views.signup, name="signup"),
    path('api/login/', views.login, name="login"),          # compatibility endpoint
    path('api/logout/', views.logout, name="logout"),
    path('api/check-premium/', views.check_premium, name="check_premium"),

    # Weather & autocomplete
    path('api/weather/', views.get_weather, name="get_weather"),
    path('api/autocomplete/', views.autocomplete, name="autocomplete"),

    # JWT Token endpoints (use our custom obtain view)
    path('api/token/', views.CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
        # Change password
    path('api/change-password/', views.change_password, name="change_password"),
        # Delete account
    path('api/delete-account/', views.delete_account, name="delete_account"),


]
