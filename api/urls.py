from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'vaccines',       views.VaccineViewSet)
router.register(r'announcements',  views.AnnouncementViewSet)
router.register(r'patients',       views.PatientViewSet)
router.register(r'notifications',  views.NotificationViewSet)
router.register(r'usage-reports',  views.VaccineUsageReportViewSet)
router.register(r'stock-reports',  views.StockLevelReportViewSet)
router.register(r'records',        views.VaccinationHistoryViewSet)
router.register(r'schedules',      views.DoseScheduleViewSet)
router.register(r'registrations',  views.RegistrationViewSet)
router.register(r'suppliers',      views.SupplierViewSet)
router.register(r'orders',         views.VaccineOrderViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('login/',     views.login_view,     name='login'),
    path('register/',  views.register_view,  name='register'),
    path('protected/', views.protected_view, name='protected'),
]