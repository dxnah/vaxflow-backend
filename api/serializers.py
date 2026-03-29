from rest_framework import serializers
from .models import Vaccine, Announcement, Patient

class VaccineSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Vaccine
        fields = '__all__'

class AnnouncementSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Announcement
        fields = '__all__'

class PatientSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Patient
        fields = ['id', 'name', 'username', 'role']