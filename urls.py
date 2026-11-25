from django.contrib import admin
from django.urls import path, include
import debug_toolbar
from django.conf import settings
from django.conf.urls.static import static


handler403 = "app.views.custom_403"
handler404 = "app.views.custom_404"
handler500 = "app.views.custom_500"

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('app.urls')),
    path('__debug__/', include(debug_toolbar.urls)),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)