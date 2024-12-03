from django.contrib.contenttypes.models import ContentType
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.exceptions import NotFound
from rest_framework.generics import ListAPIView

from .models import QuestionAnswer
from .serializers import QuestionAnswerSerializer


@extend_schema(
    parameters=[
        OpenApiParameter(
            name="content_type",
            description="The content type of the territory (e.g. 'city', 'department', 'academy')",
            required=True,
            type=str,
        ),
        OpenApiParameter(
            name="object_id",
            description="The ID of the specific territory (e.g. City ID, Department ID, Academy ID)",
            required=True,
            type=int,
        ),
    ]
)
class QuestionAnswerListByTerritoryAPIView(ListAPIView):
    serializer_class = QuestionAnswerSerializer

    def get_queryset(self):
        content_type = self.request.query_params.get("content_type")
        object_id = self.request.query_params.get("object_id")

        if not content_type or not object_id:
            raise NotFound("Both 'content_type' and 'object_id' parameters are required.")

        try:
            content_type_instance = ContentType.objects.get(model=content_type.lower())
        except ContentType.DoesNotExist:
            raise NotFound(f"Invalid content_type: {content_type}")

        return QuestionAnswer.objects.filter(content_type=content_type_instance, object_id=object_id)
