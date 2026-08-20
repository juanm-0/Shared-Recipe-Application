from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Recipe, Review
from .serializers import ReviewReadSerializer, ReviewWriteSerializer


class ReviewCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, recipe_id):
        recipe = get_object_or_404(Recipe, pk=recipe_id)
        serializer = ReviewWriteSerializer(
            data=request.data, context={"request": request, "recipe": recipe}
        )
        serializer.is_valid(raise_exception=True)
        review = serializer.save()
        output_serializer = ReviewReadSerializer(review)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)
