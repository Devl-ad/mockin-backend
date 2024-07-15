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

    referral_code = serializers.CharField(required=False, allow_blank=True)

    password = serializers.CharField(
        write_only=False, required=True, validators=[validate_password]
    )

    # confirm_password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ["fullname", "username", "email", "password", "phone", "referral_code"]

    def validate_referral_code(self, value):
        if value:
            try:
                User.objects.get(username=value)
            except User.DoesNotExist:
                raise serializers.ValidationError("Referral code does not exist.")
        return value

    def create(self, validated_data):
        # Remove password from validated_data to handle it separately
        password = validated_data.pop("password")
        ref = validated_data.pop("referral_code")
        user = User(**validated_data)
        user.set_password(password)  # Hash the password
        user.save()
        return user

    # def validate(self, attrs):
    #     password = attrs.get("password")
    #     confirm_password = attrs.pop("confirm_password", None)
    #     if password != confirm_password:
    #         raise serializers.ValidationError(
    #             {"password": "Password fields didn't match."},
    #             {"confirm_password": "Password fields didn't match."}
    #         )
    #     return attrs
