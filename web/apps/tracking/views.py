from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .models import UserInteraction
from .vector_store import add_user_interaction


@api_view(['POST'])
@permission_classes([AllowAny])
def log_interaction(request):
    """
    POST /api/v1/tracking/interaction/
    Body: {product_id, interaction_type, session_id?, search_query?}
    """
    product_id = request.data.get('product_id')
    interaction_type = request.data.get('interaction_type', 'View')
    session_id = request.data.get('session_id', '')
    search_query = request.data.get('search_query', '')

    if not product_id:
        return Response({'error': 'product_id required'}, status=400)

    user = request.user if request.user.is_authenticated else None

    # Lưu vào MySQL
    UserInteraction.objects.create(
        user=user,
        session_id=session_id,
        product_id=product_id,
        interaction_type=interaction_type,
        search_query=search_query or None,
    )

    # Nếu user đã login → lưu vào ChromaDB để personalization
    if user:
        add_user_interaction(
            user_id=str(user.id),
            product_id=product_id,
            interaction_type=interaction_type,
            search_query=search_query,
        )

    return Response({'status': 'ok'}, status=201)


@api_view(['POST'])
@permission_classes([AllowAny])
def log_checkout(request):
    """POST /api/v1/tracking/checkout/"""
    items = request.data.get('items', [])
    session_id = request.data.get('session_id', '')
    user = request.user if request.user.is_authenticated else None

    for item in items:
        pid = item.get('product_id')
        if pid:
            UserInteraction.objects.create(
                user=user, session_id=session_id,
                product_id=pid, interaction_type='Buy',
                interaction_value=item.get('quantity', 1),
            )
            if user:
                add_user_interaction(str(user.id), pid, 'Buy', '')

    return Response({'status': 'ok', 'count': len(items)}, status=201)
