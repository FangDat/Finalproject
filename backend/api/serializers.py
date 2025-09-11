from rest_framework import serializers
from .models import User

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'is_premium']
        extra_kwargs = {
            'password': {'write_only': True},
            'is_premium': {'read_only': True}
        }

    def create(self, validated_data):
        user = User(**validated_data)
        user.save()
        return user
