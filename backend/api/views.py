from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.decorators import api_view
from django.contrib.auth.hashers import check_password, make_password
from .models import User
from .serializers import UserSerializer
from django.contrib.auth import authenticate, login as dj_login, logout as dj_logout
from django.contrib.auth.hashers import check_password
from django.contrib.auth import login as dj_login

# ---------------------------
# SIGNUP
# ---------------------------
@api_view(['POST'])
def signup(request):
    print("DEBUG request.data:", request.data)   # 👈 in ra dữ liệu nhận được
    serializer = UserSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        return Response({"message": "User created successfully"}, status=201)
    else:
        print("DEBUG serializer.errors:", serializer.errors)  # 👈 in lỗi chi tiết
        return Response(serializer.errors, status=400)


# ---------------------------
# LOGIN
# ---------------------------
@api_view(['POST'])
def login(request):
    username = request.data.get("username")
    password = request.data.get("password")

    if not username or not password:
        return Response({"error": "Username and password are required"}, status=400)

    try:
        user = User.objects.get(username=username)
        if check_password(password, user.password):
            # ---------------------------
            # SESSION-BASED LOGIN
            # ---------------------------
            request.session['user_id'] = str(user._id)
            request.session['username'] = user.username
            request.session['is_premium'] = getattr(user, 'is_premium', False)

            return Response({
                "message": "Login successful",
                "user": user.username,
                "is_premium": request.session['is_premium']
            })
        else:
            return Response({"error": "Invalid password"}, status=400)
    except User.DoesNotExist:
        return Response({"error": "User not found"}, status=404)


# ---------------------------
# LOGOUT
# ---------------------------
@api_view(['POST'])
def logout(request):
    """
    Logout user và xóa toàn bộ session.
    """
    request.session.flush()
    return Response({"message": "Logged out successfully"})


# ---------------------------
# CHECK PREMIUM
# ---------------------------
@api_view(['GET'])
def check_premium(request):
    """
    Kiểm tra user hiện tại có quyền premium hay không.
    Trả về: {"is_premium": True/False}
    """
    is_premium = request.session.get('is_premium', False)
    return Response({"is_premium": is_premium})


# from django.shortcuts import render
# from rest_framework.response import Response
# from rest_framework.decorators import api_view
# from django.contrib.auth.hashers import check_password
# from .models import User
# from .serializers import UserSerializer


# @api_view(['POST'])
# def signup(request):
#     serializer = UserSerializer(data=request.data)
#     if serializer.is_valid():
#         serializer.save()
#         return Response({"message": "User created successfully!"}, status=201)
#     return Response(serializer.errors, status=400)


# @api_view(['POST'])
# def login(request):
#     username = request.data.get("username")
#     password = request.data.get("password")
#     try:
#         user = User.objects.get(username=username)
#         if check_password(password, user.password):
#             return Response({"message": "Login successful", "user": user.username})
#         else:
#             return Response({"error": "Invalid password"}, status=400)
#     except User.DoesNotExist:
#         return Response({"error": "User not found"}, status=404)


# # Create your views here.
# @api_view(['POST'])
# def signup(request):
#     print("DEBUG request.data:", request.data)  # 👈 in ra dữ liệu nhận được
#     serializer = UserSerializer(data=request.data)
#     if serializer.is_valid():
#         user = serializer.save()
#         return Response({"message": "User created successfully"}, status=201)
#     else:
#         print("DEBUG serializer.errors:", serializer.errors)  # 👈 in lỗi chi tiết
#         return Response(serializer.errors, status=400)

