from django.contrib import admin
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from backend.api.views.verifyotp_views import send_otp, verify_otp, resend_otp

from backend.api.views.map_views import get_weather_map, proxy_tile
# import các view đã tách
from backend.api.views.auth_views import (
    signup, login, logout, refresh_token,
    change_password, delete_account,
    check_premium, CustomTokenObtainPairView, user_info
)

from backend.api.views.weather_views import (
    get_weather, autocomplete_local, add_search_history, list_search_history, clear_search_history
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
    path('api/autocomplete_local/', autocomplete_local, name="autocomplete_local"),
    path('api/search-history/add/', add_search_history, name="add_search_history"),
    path('api/search-history/list/', list_search_history, name="list_search_history"),
    path('api/search-history/clear/', clear_search_history, name="clear_search_history_all"),
    path('api/search-history/clear/<str:history_id>/', clear_search_history, name="clear_search_history_item"),
    
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
    path("api/map/", get_weather_map, name="get_weather_map"),
    path("api/map/tile/", proxy_tile, name="proxy_tile"), 
    # path("api/map/preload/", preload_map_frames, name="preload_map_frames"),
    # path("api/map/current/", get_current_weather_for_map, name="get_current_weather_for_map"),
    
    path('api/send-otp/', send_otp, name="send_otp"),
    path('api/verify-otp/', verify_otp, name="verify_otp"),
    path('api/resend-otp/', resend_otp, name="resend_otp"),
    
    path('api/user-info/', user_info, name="user_info"),

]