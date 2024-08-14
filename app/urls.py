from django.urls import path
from . import views

urlpatterns = [
    path('admin/app/get_mailbox_settings/', views.get_mailbox_settings, name='get_mailbox_settings'),
    path('admin/app/save_mailbox_settings/', views.save_mailbox_settings, name='save_mailbox_settings'),
]
