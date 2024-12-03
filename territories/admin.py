from django.contrib import admin

from .models import Academy, City, Department

admin.site.register(City)
admin.site.register(Department)
admin.site.register(Academy)
