from rest_framework import serializers
from .models import (
    Vaccine,
    VaccineBatch,
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


class VaccineBatchSerializer(serializers.ModelSerializer):
    class Meta:
        model  = VaccineBatch
        fields = '__all__'


class VaccineSerializer(serializers.ModelSerializer):
    # Nest all batches inside each vaccine response
    batches = VaccineBatchSerializer(many=True, read_only=True)

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
    # Django names the FK field "vaccine" (the model attribute name).
    # FastAPI names it "vaccine_id" (the column name).
    # Adding vaccine_id as an explicit read/write alias makes both backends
    # return the same field name, so the frontend works against either.
    vaccine_id = serializers.PrimaryKeyRelatedField(
        source='vaccine',
        queryset=Vaccine.objects.all(),
        allow_null=True,
        required=False,
    )

    class Meta:
        model  = VaccineUsageReport
        # List fields explicitly so we control the name: vaccine_id instead of vaccine
        fields = [
            'id',
            'vaccine_id',     # ← exposed as vaccine_id (not vaccine) to match FastAPI
            'administered',
            'wasted',
            'remaining',
            'period',
            'report_date',
            'created_at',
        ]


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