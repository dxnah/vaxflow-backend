from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'vaccines',       views.VaccineViewSet)
router.register(r'batches',        views.VaccineBatchViewSet)
router.register(r'announcements',  views.AnnouncementViewSet)
router.register(r'patients',       views.PatientViewSet)
router.register(r'notifications',  views.NotificationViewSet)
router.register(r'usage-reports',  views.VaccineUsageReportViewSet)
router.register(r'stock-reports',  views.StockLevelReportViewSet)
router.register(r'patient-history',        views.VaccinationHistoryViewSet)
router.register(r'schedules',      views.DoseScheduleViewSet)
router.register(r'registrations',  views.RegistrationViewSet)
router.register(r'suppliers',      views.SupplierViewSet)
router.register(r'orders',         views.VaccineOrderViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('login/',                                views.login_view,                name='login'),
    path('signup/',                               views.signup_view,               name='signup'),
    path('protected/',                            views.protected_view,            name='protected'),
    path('submit-registration/',                  views.submit_registration,       name='submit-registration'),
    path('patient-registrations/<str:username>/', views.get_patient_registrations, name='patient-registrations'),
]