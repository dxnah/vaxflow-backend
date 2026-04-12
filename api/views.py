from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from django.utils import timezone
from django.contrib.auth import authenticate
from .models import (
    Vaccine, VaccineBatch, Announcement, Patient,
    Notification, VaccineUsageReport, StockLevelReport,
    VaccinationHistory, DoseSchedule, Registration,
    Supplier, VaccineOrder,
)
from .serializers import (
    VaccineSerializer, VaccineBatchSerializer, AnnouncementSerializer,
    PatientSerializer, NotificationSerializer, VaccineUsageReportSerializer,
    StockLevelReportSerializer, VaccinationHistorySerializer,
    DoseScheduleSerializer, RegistrationSerializer,
    SupplierSerializer, VaccineOrderSerializer,
)


class VaccineViewSet(viewsets.ModelViewSet):
    queryset         = Vaccine.objects.all()
    serializer_class = VaccineSerializer

    # POST  /api/vaccines/{id}/batches/  — add a batch to this vaccine
    @action(detail=True, methods=['post'], url_path='batches')
    def add_batch(self, request, pk=None):
        vaccine = self.get_object()
        data = request.data.copy()
        data['vaccine'] = vaccine.id
        serializer = VaccineBatchSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class VaccineBatchViewSet(viewsets.ModelViewSet):
    queryset         = VaccineBatch.objects.all()
    serializer_class = VaccineBatchSerializer


class AnnouncementViewSet(viewsets.ModelViewSet):
    queryset         = Announcement.objects.all()
    serializer_class = AnnouncementSerializer

class PatientViewSet(viewsets.ModelViewSet):
    queryset         = Patient.objects.all()
    serializer_class = PatientSerializer

class NotificationViewSet(viewsets.ModelViewSet):
    queryset         = Notification.objects.all()
    serializer_class = NotificationSerializer

class VaccineUsageReportViewSet(viewsets.ModelViewSet):
    queryset         = VaccineUsageReport.objects.all()
    serializer_class = VaccineUsageReportSerializer

class StockLevelReportViewSet(viewsets.ModelViewSet):
    queryset         = StockLevelReport.objects.all()
    serializer_class = StockLevelReportSerializer

class VaccinationHistoryViewSet(viewsets.ModelViewSet):
    queryset         = VaccinationHistory.objects.all()
    serializer_class = VaccinationHistorySerializer

class DoseScheduleViewSet(viewsets.ModelViewSet):
    queryset         = DoseSchedule.objects.all()
    serializer_class = DoseScheduleSerializer

class RegistrationViewSet(viewsets.ModelViewSet):
    queryset         = Registration.objects.all()
    serializer_class = RegistrationSerializer

class SupplierViewSet(viewsets.ModelViewSet):
    queryset         = Supplier.objects.all()
    serializer_class = SupplierSerializer

class VaccineOrderViewSet(viewsets.ModelViewSet):
    queryset         = VaccineOrder.objects.all()
    serializer_class = VaccineOrderSerializer


# ── Protected endpoint ────────────────────────────────────────────────────────
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def protected_view(request):
    return Response({"message": "Authorized — you are logged in!"})


@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    username = request.data.get('username')
    password = request.data.get('password')

    user = authenticate(username=username, password=password)
    if user:
        return Response({
            'message': 'Login successful',
            'username': user.username,
            'role': 'admin'
        })

    try:
        patient = Patient.objects.get(username=username, password=password)
        patient.last_login = timezone.now()
        patient.save()
        return Response({
            'message': 'Login successful',
            'user': PatientSerializer(patient).data,
            'role': 'patient'
        })
    except Patient.DoesNotExist:
        return Response(
            {'error': 'Invalid username or password'},
            status=status.HTTP_401_UNAUTHORIZED
        )


@api_view(['POST'])
@permission_classes([AllowAny])
def signup_view(request):
    username = request.data.get('username')
    password = request.data.get('password')
    name     = request.data.get('name')
    email    = request.data.get('email', '')
    phone    = request.data.get('phone', '')

    if not username or not password or not name:
        return Response(
            {'error': 'username, password, and name are required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    if Patient.objects.filter(username=username).exists():
        return Response(
            {'error': 'Username already exists'},
            status=status.HTTP_400_BAD_REQUEST
        )
    patient = Patient.objects.create(
        username=username,
        password=password,
        name=name,
        email=email,
        phone=phone,
        role='patient'
    )
    return Response({
        'message': 'Account created successfully',
        'user': PatientSerializer(patient).data
    }, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([AllowAny])
def submit_registration(request):
    username = request.data.get('username')
    patient = None
    if username:
        try:
            patient = Patient.objects.get(username=username)
        except Patient.DoesNotExist:
            pass

    count = Registration.objects.count()
    queue_number = f'Q-{str(count + 1).zfill(3)}'

    data = request.data.copy()
    serializer = RegistrationSerializer(data=data)
    if serializer.is_valid():
        serializer.save(patient=patient, queue_number=queue_number)
        return Response({
            'message': 'Registration submitted successfully',
            'queue_number': queue_number,
            'registration': serializer.data
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_patient_registrations(request, username):
    try:
        patient = Patient.objects.get(username=username)
        regs = Registration.objects.filter(patient=patient).order_by('created_at')
        serializer = RegistrationSerializer(regs, many=True)
        return Response(serializer.data)
    except Patient.DoesNotExist:
        return Response({'error': 'Patient not found'}, status=status.HTTP_404_NOT_FOUND)