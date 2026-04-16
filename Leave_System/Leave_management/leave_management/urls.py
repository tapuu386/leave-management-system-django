from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('apps.accounts.urls')),
    path('accounts/', include('apps.accounts.urls')),
    path('dashboard/', include('apps.leaves.urls')),
    path('hr/', include('apps.employees.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
