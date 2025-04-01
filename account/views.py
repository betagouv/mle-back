from rest_framework import viewsets

from .models import Owner
from .serializers import OwnerSerializer


class OwnerViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Owner.objects.all()
    serializer_class = OwnerSerializer
