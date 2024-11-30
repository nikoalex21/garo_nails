from django.contrib import admin
from .models import Pago

class PagoAdmin(admin.ModelAdmin):
    list_display = ('trabajador', 'monto', 'fecha')  
    search_fields = ('monto',)


admin.site.register(Pago, PagoAdmin)
