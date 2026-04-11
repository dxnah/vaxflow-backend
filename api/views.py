from rest_framework import viewsets, status
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from .models import (
    Vaccine, Announcement, Patient,
    Notification, VaccineUsageReport, StockLevelReport,
    VaccinationHistory, DoseSchedule, Registration,
    Supplier, VaccineOrder,
)
from .serializers import (
    VaccineSerializer, AnnouncementSerializer, PatientSerializer,
    NotificationSerializer, VaccineUsageReportSerializer,
    StockLevelReportSerializer, VaccinationHistorySerializer,
    DoseScheduleSerializer, RegistrationSerializer,
    SupplierSerializer, VaccineOrderSerializer,
)


class VaccineViewSet(viewsets.ModelViewSet):
    queryset         = Vaccine.objects.all()
    serializer_class = VaccineSerializer

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


# ── Login ─────────────────────────────────────────────────────────────────────
@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    username = request.data.get('username')
    password = request.data.get('password')
    try:
        patient = Patient.objects.get(username=username, password=password)
        patient.last_login = timezone.now()
        patient.save()
        return Response({
            'message': 'Login successful',
            'user': PatientSerializer(patient).data
        })
    except Patient.DoesNotExist:
        return Response(
            {'error': 'Invalid username or password'},
            status=status.HTTP_401_UNAUTHORIZED
        )


# ── Register ──────────────────────────────────────────────────────────────────
@api_view(['POST'])
@permission_classes([AllowAny])
def register_view(request):
    username = request.data.get('username')
    password = request.data.get('password')
    name     = request.data.get('name')

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
        role='patient'
    )
    return Response({
        'message': 'Registration successful',
        'user': PatientSerializer(patient).data
    }, status=status.HTTP_201_CREATED)


# ── Patient Registration (with queue number) ──────────────────────────────────
@api_view(['POST'])
@permission_classes([AllowAny])
def submit_registration(request):
    username = request.data.get('username')

    # Get patient if logged in
    patient = None
    if username:
        try:
            patient = Patient.objects.get(username=username)
        except Patient.DoesNotExist:
            pass

    # Generate sequential queue number
    count = Registration.objects.count()
    queue_number = f'Q-{str(count + 1).zfill(3)}'

    data = request.data.copy()
    serializer = RegistrationSerializer(data=data)
    if serializer.is_valid():
        serializer.save(
            patient=patient,
            queue_number=queue_number
        )
        return Response({
            'message': 'Registration submitted successfully',
            'queue_number': queue_number,
            'registration': serializer.data
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ── Get registrations by patient ──────────────────────────────────────────────
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