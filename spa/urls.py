from django.urls import path
from .views import lista_servicios, crear_solicitud, solicitudes_admin, asignar_trabajador,register_superuser,  custom_login, custom_logout, solicitudes_trabajador, registrar_trabajador, servicios_trabajador, aceptar_solicitud, rechazar_solicitud,obtener_horarios_disponibles, contabilidad, toggle_trabajador_activo,guardar_monto_trabajador, crear_solicitud_admin

urlpatterns = [
    path('', lista_servicios, name='lista_servicios'),
    path('solicitar/', crear_solicitud, name='crear_solicitud'),
    path('solicitudes/', solicitudes_admin, name='solicitudes_admin'),
    path('asignar_trabajador/<int:solicitud_id>/', asignar_trabajador, name='asignar_trabajador'),
    path('login/', custom_login, name='login'),
    path('logout/', custom_logout, name='logout'),
    path('register/superuser/', register_superuser, name='register_superuser'),
    path('trabajador/solicitudes/', solicitudes_trabajador, name='solicitudes_trabajador'),
    path('registrar_trabajador/', registrar_trabajador, name='registrar_trabajador'),
    path('trabajador/servicios/', servicios_trabajador, name='servicios_trabajador'),
    path('aceptar_solicitud/<int:solicitud_id>/', aceptar_solicitud, name='aceptar_solicitud'),
    path('rechazar_solicitud/<int:solicitud_id>/', rechazar_solicitud, name='rechazar_solicitud'),
    path('obtener_horarios/', obtener_horarios_disponibles, name='obtener_horarios'),
    path('toggle_trabajador_activo/<int:trabajador_id>/', toggle_trabajador_activo, name='toggle_trabajador_activo'),
    path('guardar_monto_trabajador/', guardar_monto_trabajador, name='guardar_monto_trabajador'),
    path('crear_solicitud_admin/', crear_solicitud_admin, name='crear_solicitud_admin'),

    
]
