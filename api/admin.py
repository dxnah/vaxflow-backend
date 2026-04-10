from django.contrib import admin
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

admin.site.register(Vaccine)
admin.site.register(Announcement)
admin.site.register(Patient)
admin.site.register(Notification)
admin.site.register(VaccineUsageReport)
admin.site.register(StockLevelReport)
admin.site.register(VaccinationHistory)
admin.site.register(DoseSchedule)
admin.site.register(Registration)
admin.site.register(Supplier)
admin.site.register(VaccineOrder)