import jwt
from .models import User
from .serializers import SignUpSerializer, SignInSerializer
from .utils import account_verification_mail, password_reset_mail
from decouple import config
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.shortcuts import get_current_site
from django.shortcuts import render
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

@api_view(["POST"])
def sign_up(request):
    if request.method == "POST":
        serializer = SignUpSerializer(data=request.data)

        if serializer.is_valid(raise_exception=True):
            serializer.save()

            current_site = get_current_site(request).domain
            relative_link = reverse("verify_user")
            user = User.objects.get(email=serializer.validated_data["email"])
            token = RefreshToken.for_user(user)
            absolute_url = f'http://{current_site}{relative_link}?token={token}'
            link = str(absolute_url)
            account_verification_mail(email=user.email, link=link, first_name=user.first_name)

            return Response(
                {
                    "success":True,
                    "data":serializer.data
                }, status=status.HTTP_201_CREATED
            )
        return Response(
            {
                "success":False,
                "data":serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST
        )


@api_view(["GET"])
def verify_user(request):
    if request.method == "GET":
        token = request.GET.get("token")

        try:
            payload = jwt.decode(token, config("SECRET_KEY"), algorithms=["HS256"])
            user = User.objects.get(id=payload["user_id"])

            if not user.is_verified:
                user.is_verified = True
                user.save()

            return Response (
                {
                'success':True,
                'message':'Email verified successfully.'
                }, status=status.HTTP_200_OK
            )
        except jwt.ExpiredSignatureError as e:
            return Response(
                {
                    'success':False,
                    'message':'Activation link expired'
                }, status=status.HTTP_400_BAD_REQUEST
            )
        except jwt.exceptions.DecodeError as e:
            return Response(
                {
                    'success':False,
                    'message':'Invalid token'
                }, status=status.HTTP_400_BAD_REQUEST
            )
        except jwt.exceptions.InvalidTokenError as e:
            return Response(
                {
                    'success':False,
                    'message':'Invalid token'
                }, status=status.HTTP_400_BAD_REQUEST
            )
        except User.DoesNotExist as e:
            return Response(
                {
                    'success':False,
                    'message':'User not found'
                }, status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {
                    'success':False,
                    'message':str(e)
                }, status=status.HTTP_400_BAD_REQUEST
            )


@api_view(["POST"])
def login(request):
    if request.method == "POST":
        serializer = SignInSerializer(data=request.data)

        if serializer.is_valid(raise_exception=True):
            tokens = serializer.generate_tokens(serializer.validated_data)

            return Response (
                {
                    "success":True,
                    "tokens":tokens
                }, status=status.HTTP_200_OK
            )


@api_view(["POST"])
def password_reset(request):
    if request.method == "POST":
        email = request.data.get("email")

        if not email:
            return Response(
                {
                    "success":True,
                    "message":"Email is required"
                }, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = User.objects.get(email=email)
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            current_site = get_current_site(request).domain
            relative_link = reverse("password_reset_confirm")
            absolute_url = f'http://{current_site}{relative_link}?uid={uid}&token={token}'
            link = str(absolute_url)
            password_reset_mail(email=user.email, first_name=user.first_name, link=link)

            return Response(
                {
                    'success':True,
                    'message':'Password reset mail sent'
                }, status=status.HTTP_200_OK
            )
        except User.DoesNotExist as e:
            return Response (
                {
                    'success':False,
                    'message':'User does not exist'
                }, status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response (
                {
                    'success':False,
                    'message':str(e)
                }, status=status.HTTP_400_BAD_REQUEST
            )

@api_view(["PUT", "PATCH"])
def password_reset_confirm(request):
    if request.method == "PUT" or request.method == "PATCH":
        uid = request.data.get('uid')
        token = request.data.get('token')
        password = request.data.get('password')

        if not uid or not token or not password:
            return Response (
                {
                    'success':False,
                    'message':'All fields are required'
                }, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user_id = urlsafe_base64_decode(uid)
            user = User.objects.get(id=uid)

            if not default_token_generator.check_token(user, token):
                return Response (
                    {
                        "success":True,
                        "message":"Invalid token"
                    }, status=status.HTTP_400_BAD_REQUEST                
                )

            user.set_password(password)
            user.save()

            return Response(
                {
                    'success':True,
                    'message':'Password reset successful'
                }, status=status.HTTP_200_OK
            )
        except User.DoesNotExist as e:
            return Response (
                {
                    'success':False,
                    'message':'User does not exist'
                }, status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response (
                {
                    'success':False,
                    'message':str(e)
                }, status=status.HTTP_400_BAD_REQUEST
            )

            
