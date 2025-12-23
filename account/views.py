from rest_framework import viewsets

from .models import Owner
from .serializers import OwnerSerializer

from rest_framework import generics
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework import status

from .serializers import StudentRegistrationSerializer


class OwnerViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Owner.objects.all()
    serializer_class = OwnerSerializer


class StudentRegistrationView(generics.GenericAPIView):
    serializer_class = StudentRegistrationSerializer
    permission_classes = [permissions.AllowAny]
    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"message": "Student registered successfully"}, status=status.HTTP_201_CREATED)
