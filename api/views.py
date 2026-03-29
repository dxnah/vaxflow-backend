from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import Vaccine, Announcement, Patient
from .serializers import VaccineSerializer, AnnouncementSerializer, PatientSerializer


# ── Vaccines ──────────────────────────────────────────────────────────────────

@api_view(['GET', 'POST'])
def vaccine_list(request):
    if request.method == 'GET':
        vaccines   = Vaccine.objects.all()
        serializer = VaccineSerializer(vaccines, many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        serializer = VaccineSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def vaccine_detail(request, pk):
    try:
        vaccine = Vaccine.objects.get(pk=pk)
    except Vaccine.DoesNotExist:
        return Response(
            {'error': 'Vaccine not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    serializer = VaccineSerializer(vaccine)
    return Response(serializer.data)


# ── Announcements ─────────────────────────────────────────────────────────────

@api_view(['GET', 'POST'])
def announcement_list(request):
    if request.method == 'GET':
        announcements = Announcement.objects.all()
        serializer    = AnnouncementSerializer(announcements, many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        serializer = AnnouncementSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def announcement_detail(request, pk):
    try:
        announcement = Announcement.objects.get(pk=pk)
    except Announcement.DoesNotExist:
        return Response(
            {'error': 'Announcement not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    serializer = AnnouncementSerializer(announcement)
    return Response(serializer.data)

# ── Patients ──────────────────────────────────────────────────────────────────

@api_view(['GET'])
def patient_list(request):
    patients   = Patient.objects.all()
    serializer = PatientSerializer(patients, many=True)
    return Response(serializer.data)


# ── Login ─────────────────────────────────────────────────────────────────────

@api_view(['POST'])
def login_view(request):
    username = request.data.get('username')
    password = request.data.get('password')
    try:
        patient = Patient.objects.get(username=username, password=password)
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