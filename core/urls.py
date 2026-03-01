# Trabalho-PDS/core/urls.py
from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('clinica.urls')),
    path('login/', auth_views.LoginView.as_view(template_name='clinica/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
]
# Isso permite que o Django sirva os arquivos durante o desenvolvimento
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])