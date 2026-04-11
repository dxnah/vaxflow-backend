from django.db import models


# ── Vaccine ───────────────────────────────────────────────────────────────────
class Vaccine(models.Model):
    STATUS_CHOICES = [
        ('in_stock',  'In Stock'),
        ('low_stock', 'Low Stock'),
        ('out_stock', 'Out of Stock'),
    ]
    name           = models.CharField(max_length=100)
    available      = models.IntegerField(default=0)
    status         = models.CharField(max_length=20, choices=STATUS_CHOICES, default='in_stock')
    batch_number   = models.CharField(max_length=100, blank=True, null=True)
    expiry_date    = models.DateField(blank=True, null=True)
    ml_recommended = models.IntegerField(default=0)
    min_stock      = models.IntegerField(default=0)
    created_at     = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    def __str__(self):
        return self.name


# ── Announcement ──────────────────────────────────────────────────────────────
class Announcement(models.Model):
    title      = models.CharField(max_length=200)
    message    = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    def __str__(self):
        return self.title


# ── Patient ───────────────────────────────────────────────────────────────────
class Patient(models.Model):
    username   = models.CharField(max_length=100, unique=True)
    password   = models.CharField(max_length=100)
    name       = models.CharField(max_length=200)
    role       = models.CharField(max_length=20, default='patient')
    email      = models.CharField(max_length=200, blank=True, null=True)
    phone      = models.CharField(max_length=20, blank=True, null=True)
    status     = models.CharField(max_length=20, default='Active')
    last_login = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    def __str__(self):
        return self.name


# ── Notification ──────────────────────────────────────────────────────────────
class Notification(models.Model):
    TYPE_CHOICES = [
        ('critical', 'Critical'),
        ('warning',  'Warning'),
        ('info',     'Info'),
        ('success',  'Success'),
    ]
    title      = models.CharField(max_length=200)
    message    = models.TextField()
    type       = models.CharField(max_length=20, choices=TYPE_CHOICES, default='info')
    read       = models.BooleanField(default=False)
    vaccine    = models.ForeignKey(
        'Vaccine',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='notifications'
    )
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    def __str__(self):
        return self.title


# ── VaccineUsageReport ────────────────────────────────────────────────────────
class VaccineUsageReport(models.Model):
    vaccine      = models.ForeignKey(
        'Vaccine',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='usage_reports'
    )
    administered = models.IntegerField(default=0)
    wasted       = models.IntegerField(default=0)
    remaining    = models.IntegerField(default=0)
    period       = models.CharField(max_length=50, default='monthly')
    report_date  = models.DateField(blank=True, null=True)
    created_at   = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    def __str__(self):
        return f"{self.vaccine} - {self.period}"


# ── StockLevelReport ──────────────────────────────────────────────────────────
class StockLevelReport(models.Model):
    date         = models.DateField(blank=True, null=True)
    period_label = models.CharField(max_length=50, blank=True, null=True)
    in_stock     = models.IntegerField(default=0)
    low_stock    = models.IntegerField(default=0)
    out_stock    = models.IntegerField(default=0)
    created_at   = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    def __str__(self):
        return f"Stock Report - {self.period_label}"


# ── VaccinationHistory ────────────────────────────────────────────────────────
class VaccinationHistory(models.Model):
    patient         = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name='records'
    )
    vaccine         = models.ForeignKey(
        'Vaccine',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='vaccination_records'
    )
    dose            = models.CharField(max_length=50)
    date            = models.DateField(blank=True, null=True)
    facility        = models.CharField(max_length=200)
    administered_by = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.patient.name} - {self.vaccine} {self.dose}"


# ── DoseSchedule ──────────────────────────────────────────────────────────────
class DoseSchedule(models.Model):
    patient     = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name='schedules'
    )
    dose_name   = models.CharField(max_length=50)
    dose_date   = models.DateField(blank=True, null=True)
    completed   = models.BooleanField(default=False)
    is_optional = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.patient.name} - {self.dose_name}"


# ── Registration ──────────────────────────────────────────────────────────────
class Registration(models.Model):
    patient           = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name='registrations',
        null=True, blank=True
    )
    full_name         = models.CharField(max_length=200)
    age               = models.CharField(max_length=10)
    birthdate         = models.DateField(blank=True, null=True)
    address           = models.TextField()
    contact           = models.CharField(max_length=20)
    incident_date     = models.DateField(blank=True, null=True)
    injury_type       = models.CharField(max_length=50)
    animal_type       = models.CharField(max_length=50)
    animal_owner      = models.CharField(max_length=100)
    animal_vaccinated = models.CharField(max_length=20)
    body_part         = models.TextField()
    queue_number      = models.CharField(max_length=10, blank=True, null=True)
    created_at        = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    def __str__(self):
        return f"{self.full_name} - {str(self.incident_date)}"


# ── Supplier ──────────────────────────────────────────────────────────────────
class Supplier(models.Model):
    STATUS_CHOICES = [
        ('Active',   'Active'),
        ('Inactive', 'Inactive'),
    ]
    name           = models.CharField(max_length=200)
    contact        = models.EmailField(max_length=200, blank=True, null=True)
    phone          = models.CharField(max_length=50, blank=True, null=True)
    address        = models.TextField(blank=True, null=True)
    vaccines       = models.TextField(blank=True, null=True)
    status         = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Active')
    lead_time_days = models.IntegerField(default=0)
    notes          = models.TextField(blank=True, null=True)
    created_at     = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    def __str__(self):
        return self.name


# ── VaccineOrder ──────────────────────────────────────────────────────────────
class VaccineOrder(models.Model):
    STATUS_CHOICES = [
        ('Pending',   'Pending'),
        ('Approved',  'Approved'),
        ('Shipped',   'Shipped'),
        ('Delivered', 'Delivered'),
        ('Cancelled', 'Cancelled'),
    ]
    vaccine        = models.ForeignKey(
        'Vaccine',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='orders'
    )
    supplier       = models.ForeignKey(
        'Supplier',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='orders'
    )
    amount         = models.IntegerField(default=0)
    price_per_dose = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total          = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status         = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    ordered_at     = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    def __str__(self):
        return f"Order #{self.id} - {self.vaccine} ({self.status})"