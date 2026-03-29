from django.contrib import admin
from .models import Vaccine, Announcement, Patient

admin.site.register(Vaccine)
admin.site.register(Announcement)
admin.site.register(Patient)