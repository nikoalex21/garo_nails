# spa/admin.py
from django.contrib import admin
from .models import Servicio, Solicitud,Trabajador

class ServicioAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'precio', 'tiempo_estimado')  
    search_fields = ('nombre',)  
class SolicitudAdmin(admin.ModelAdmin):
    list_display = ('cliente', 'telefono', 'fecha', 'hora', 'servicio','estado') 
    list_filter = ('fecha', 'servicio') 
    
class TrabajadorAdmin(admin.ModelAdmin):
    list_display = ('nombre','user', 'telefono')
    filter_horizontal = ('servicios',)

admin.site.register(Trabajador, TrabajadorAdmin)
admin.site.register(Servicio, ServicioAdmin)  
admin.site.register(Solicitud, SolicitudAdmin)  


