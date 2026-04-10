from rest_framework import serializers
from .models import (
    Vaccine,
    Announcement,
    Patient,
    Notification,
    VaccineUsageReport,
    StockLevelReport,
    VaccinationHistory,
    DoseSchedule,
    Registration,
    Supplier,
    VaccineOrder,
)


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
        fields = ['id', 'name', 'username', 'role',
                  'email', 'phone', 'status', 'last_login', 'created_at']


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Notification
        fields = '__all__'


class VaccineUsageReportSerializer(serializers.ModelSerializer):
    class Meta:
        model  = VaccineUsageReport
        fields = '__all__'


class StockLevelReportSerializer(serializers.ModelSerializer):
    class Meta:
        model  = StockLevelReport
        fields = '__all__'


class VaccinationHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model  = VaccinationHistory
        fields = '__all__'


class DoseScheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model  = DoseSchedule
        fields = '__all__'


class RegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Registration
        fields = '__all__'


class SupplierSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Supplier
        fields = '__all__'


class VaccineOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model  = VaccineOrder
        fields = '__all__'