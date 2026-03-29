from django.db import models

class Vaccine(models.Model):
    name      = models.CharField(max_length=100)
    available = models.IntegerField(default=0)
    status    = models.CharField(max_length=20)

    def __str__(self):
        return self.name


class Announcement(models.Model):
    title   = models.CharField(max_length=200)
    message = models.TextField()

    def __str__(self):
        return self.title


class Patient(models.Model):
    username = models.CharField(max_length=100, unique=True)
    password = models.CharField(max_length=100)
    name     = models.CharField(max_length=200)
    role     = models.CharField(max_length=20, default='patient')

    def __str__(self):
        return self.name