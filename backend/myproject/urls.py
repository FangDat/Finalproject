from django.contrib import admin
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView


# import các view đã tách
from backend.api.views.auth_views import (
    signup, login, logout, refresh_token,
    change_password, delete_account,
    check_premium, CustomTokenObtainPairView,
)

from backend.api.views.weather_views import (
    get_weather, autocomplete,
)

from backend.api.views.feedback_views import (
    send_feedback,
)

urlpatterns = [
    path('admin/', admin.site.urls),

    # Auth
    path('api/signup/', signup, name="signup"),
    path('api/login/', login, name="login"),
    path('api/logout/', logout, name="logout"),
    path('api/refresh/', refresh_token, name="refresh_token"),

    # Weather & autocomplete
    path('api/weather/', get_weather, name="get_weather"),
    path('api/autocomplete/', autocomplete, name="autocomplete"),

    # JWT (optional, mostly for debugging)
    path('api/token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # Account
    path('api/change-password/', change_password, name="change_password"),
    path('api/delete-account/', delete_account, name="delete_account"),

    # Premium
    path('api/check-premium/', check_premium, name="check_premium"),

    # Feedback
    path('api/send-feedback/', send_feedback, name="send_feedback"),
]
