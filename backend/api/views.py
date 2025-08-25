from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.decorators import api_view
from django.contrib.auth.hashers import check_password
from .models import User
from .serializers import UserSerializer

@api_view(['POST'])
def signup(request):
    serializer = UserSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response({"message": "User created successfully!"}, status=201)
    return Response(serializer.errors, status=400)

@api_view(['POST'])
def login(request):
    username = request.data.get("username")
    password = request.data.get("password")

    try:
        user = User.objects.get(username=username)
        if check_password(password, user.password):
            return Response({"message": "Login successful", "user": user.username})
        else:
            return Response({"error": "Invalid password"}, status=400)
    except User.DoesNotExist:
        return Response({"error": "User not found"}, status=404)

# Create your views here.

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

