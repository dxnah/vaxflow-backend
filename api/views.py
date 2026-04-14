from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.authtoken.models import Token
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.utils import timezone
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

    @action(detail=False, methods=['post'], url_path='mark_all_read')
    def mark_all_read(self, request):
        Notification.objects.filter(read=False).update(read=True)
        return Response({'status': 'ok'})

    @action(detail=False, methods=['delete'], url_path='clear_all')
    def clear_all(self, request):
        Notification.objects.all().delete()
        return Response(status=204)


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

    def get_queryset(self):
        username = self.request.query_params.get('username')
        if username:
            try:
                patient = Patient.objects.get(username=username)
                return DoseSchedule.objects.filter(patient=patient)
            except Patient.DoesNotExist:
                return DoseSchedule.objects.none()
        return DoseSchedule.objects.all()


class SupplierViewSet(viewsets.ModelViewSet):
    queryset         = Supplier.objects.all()
    serializer_class = SupplierSerializer


class VaccineOrderViewSet(viewsets.ModelViewSet):
    queryset         = VaccineOrder.objects.all()
    serializer_class = VaccineOrderSerializer


class RegistrationViewSet(viewsets.ModelViewSet):
    queryset         = Registration.objects.all()
    serializer_class = RegistrationSerializer

    def get_queryset(self):
        token_key = self.request.META.get('HTTP_AUTHORIZATION', '').replace('Token ', '')
        if not token_key:
            return Registration.objects.all()
        try:
            token      = Token.objects.get(key=token_key)
            patient_id = token.user.username.split('_')[-1]
            patient    = Patient.objects.get(id=patient_id)
            return Registration.objects.filter(patient=patient)
        except Exception:
            return Registration.objects.all()


@api_view(['GET'])
@permission_classes([IsAdminUser])
def admin_users_view(request):
    users = User.objects.filter(is_staff=True).values(
        'id', 'username', 'email', 'is_staff', 'is_superuser', 'last_login'
    )
    return Response(list(users))


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
        token, _ = Token.objects.get_or_create(user=user)
        return Response({
            'message':  'Login successful',
            'token':    token.key,
            'username': user.username,
            'role':     'admin'
        })

    try:
        patient = Patient.objects.get(username=username, password=password)
        patient.last_login = timezone.now()
        patient.save()
        django_user, _ = User.objects.get_or_create(username=f'patient_{patient.id}')
        token, _       = Token.objects.get_or_create(user=django_user)
        return Response({
            'message': 'Login successful',
            'token':   token.key,
            'user':    PatientSerializer(patient).data,
            'role':    'patient'
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
        username=username, password=password,
        name=name, email=email, phone=phone, role='patient'
    )
    return Response({
        'message': 'Account created successfully',
        'user': PatientSerializer(patient).data
    }, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([AllowAny])
def submit_registration(request):
    username = request.data.get('username')
    patient  = None
    if username:
        try:
            patient = Patient.objects.get(username=username)
        except Patient.DoesNotExist:
            pass

    count        = Registration.objects.count()
    queue_number = f'Q-{str(count + 1).zfill(3)}'

    data       = request.data.copy()
    serializer = RegistrationSerializer(data=data)
    if serializer.is_valid():
        serializer.save(patient=patient, queue_number=queue_number)
        return Response({
            'message':      'Registration submitted successfully',
            'queue_number': queue_number,
            'registration': serializer.data
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_patient_registrations(request, username):
    try:
        patient    = Patient.objects.get(username=username)
        regs       = Registration.objects.filter(patient=patient).order_by('created_at')
        serializer = RegistrationSerializer(regs, many=True)
        return Response(serializer.data)
    except Patient.DoesNotExist:
        return Response({'error': 'Patient not found'}, status=status.HTTP_404_NOT_FOUND)