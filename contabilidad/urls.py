from django.urls import path
from . import views

urlpatterns = [
   path('resumen_contable/', views.resumen_contable, name='resumen_contable'),
   path('pagar_trabajador/<int:trabajador_id>/', views.pagar_trabajador, name='pagar_trabajador'),
   path('servicios_trabajador/<int:trabajador_id>/', views.servicios_trabajador, name='servicios_trabajador'),
   path('inventario/', views.inventario, name='inventario'),
   path('adelanto_trabajador/', views.adelanto_trabajador, name='adelanto_trabajador'),
   path('servicios_por_intervalo/', views.servicios_por_trabajador_y_dia, name='servicios_por_intervalo'),
   path('resumen_financiero/', views.resumen_financiero, name='resumen_financiero'),
   path('historial_servicios/', views.historial_servicios, name='historial_servicios'),
   path('add-monto-adicional/', views.add_monto_adicional, name='add_monto_adicional'),
   path('cambiar-modo-pago/', views.cambiar_modo_pago, name='cambiar_modo_pago'),
]
