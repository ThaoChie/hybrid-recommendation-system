from django.contrib.auth import get_user_model, authenticate
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    email = request.data.get('email')
    username = request.data.get('username')
    password = request.data.get('password')
    if not all([email, username, password]):
        return Response({'error': 'email, username, password required'}, status=400)
    if User.objects.filter(email=email).exists():
        return Response({'error': 'Email đã tồn tại'}, status=400)

    user = User.objects.create_user(email=email, username=username, password=password)
    refresh = RefreshToken.for_user(user)
    return Response({
        'user': {'id': user.id, 'email': user.email, 'username': user.username},
        'tokens': {'access': str(refresh.access_token), 'refresh': str(refresh)}
    }, status=201)


@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    email = request.data.get('email')
    password = request.data.get('password')
    user = authenticate(request, username=email, password=password)
    if not user:
        return Response({'error': 'Email hoặc mật khẩu không đúng'}, status=401)

    refresh = RefreshToken.for_user(user)
    return Response({
        'user': {'id': user.id, 'email': user.email, 'username': user.username},
        'tokens': {'access': str(refresh.access_token), 'refresh': str(refresh)}
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def profile(request):
    u = request.user
    return Response({'id': u.id, 'email': u.email, 'username': u.username})
