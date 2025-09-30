from django.contrib import admin
from django.urls import path
from backend.api import views
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path('admin/', admin.site.urls),

    # Auth
    path('api/signup/', views.signup, name="signup"),
    path('api/login/', views.login, name="login"),
    path('api/logout/', views.logout, name="logout"),
    path('api/refresh/', views.refresh_token, name="refresh_token"),

    # Weather & autocomplete
    path('api/weather/', views.get_weather, name="get_weather"),
    path('api/autocomplete/', views.autocomplete, name="autocomplete"),

    # JWT (optional, mostly for debugging)
    path('api/token/', views.CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # Account
    path('api/change-password/', views.change_password, name="change_password"),
    path('api/delete-account/', views.delete_account, name="delete_account"),

    # Premium
    path('api/check-premium/', views.check_premium, name="check_premium"),
    
    
    path('api/send-feedback/', views.send_feedback, name="send_feedback"),
]
