from models import Stand
from django.contrib import admin

class StandAdmin(admin.ModelAdmin):
  pass

admin.site.register(Stand, StandAdmin)
