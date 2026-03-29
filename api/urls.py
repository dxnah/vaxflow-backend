from django.urls import path
from . import views

urlpatterns = [
    path('vaccines/',          views.vaccine_list,      name='vaccine-list'),
    path('vaccines/<int:pk>/', views.vaccine_detail,    name='vaccine-detail'),
    path('announcements/',     views.announcement_list, name='announcement-list'),
    path('announcements/<int:pk>/', views.announcement_detail,  name='announcement-detail'),
    path('patients/',          views.patient_list,      name='patient-list'),
    path('login/',             views.login_view,        name='login'),
    path('register/',          views.register_view,     name='register'),  
]