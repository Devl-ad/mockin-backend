from rest_framework import serializers
from django.contrib.auth import get_user_model
from rest_framework.validators import UniqueValidator
from django.contrib.auth.password_validation import validate_password


User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(
        required=True,
        validators=[
            UniqueValidator(
                queryset=User.objects.all(),
                message="A User with this Email already exist",
            )
        ],
    )

    username = serializers.CharField(
        required=True,
        validators=[
            UniqueValidator(
                queryset=User.objects.all(),
                message="A User with this Username already exist",
            )
        ],
    )

    referral = serializers.CharField(
        required=False,
    )

    password = serializers.CharField(
        write_only=False, required=True, validators=[validate_password]
    )

    # confirm_password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ["fullname", "username", "email", "password", "phone", "referral"]

    def validate_referral(self, value):
        if value:
            try:
                User.objects.get(username=value)
            except User.DoesNotExist:
                raise serializers.ValidationError("Referral code does not exist.")
        return value

    # def validate(self, attrs):
    #     password = attrs.get("password")
    #     confirm_password = attrs.pop("confirm_password", None)
    #     if password != confirm_password:
    #         raise serializers.ValidationError(
    #             {"password": "Password fields didn't match."},
    #             {"confirm_password": "Password fields didn't match."}
    #         )
    #     return attrs
