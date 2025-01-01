from rest_framework import viewsets, generics
from django.http import JsonResponse
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from .models import Income
from .serializer import IncomeStatementChartSerializer, IncomeSerializer


class IncomeListCreateView(generics.ListCreateAPIView):
    queryset = Income.objects.all()
    serializer_class = IncomeSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(business__user=self.request.user)


class IncomeDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Income.objects.all()
    serializer_class = IncomeSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(business__user=self.request.user)


class IncomeStatementChartViewSet(viewsets.ReadOnlyModelViewSet):
    def list(self, request, *args, **kwargs):
        try:
            if not request.user.is_authenticated:
                return JsonResponse({'error': 'User is not authenticated'}, status=status.HTTP_401_UNAUTHORIZED)

            serializer = IncomeStatementChartSerializer(data=request.GET, context={'request': request})
            if not serializer.is_valid():
                return JsonResponse({'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

            data = serializer.validated_data
            response_data = serializer.to_representation(data)

            return JsonResponse(response_data, safe=False, status=status.HTTP_200_OK)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
