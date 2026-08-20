from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsOwnerOrStaff

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


class ReviewDetailView(APIView):
    permission_classes = [IsAuthenticated, IsOwnerOrStaff]

    def get_object(self, recipe_id, review_id):
        review = get_object_or_404(Review, pk=review_id, recipe_id=recipe_id)
        self.check_object_permissions(self.request, review)
        return review

    def patch(self, request, recipe_id, review_id):
        review = self.get_object(recipe_id, review_id)
        serializer = ReviewWriteSerializer(
            review, data=request.data, partial=True, context={"request": request, "recipe": review.recipe}
        )
        serializer.is_valid(raise_exception=True)
        review = serializer.save()
        output_serializer = ReviewReadSerializer(review)
        return Response(output_serializer.data, status=status.HTTP_200_OK)

    def delete(self, request, recipe_id, review_id):
        review = self.get_object(recipe_id, review_id)
        review.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
