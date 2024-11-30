from django.shortcuts import render, redirect, get_object_or_404, get_list_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from .models import Servicio, Solicitud, User, Trabajador
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from datetime import datetime, timedelta, time,timedelta
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Sum
from decimal import Decimal
from datetime import date



def lista_servicios(request):
    servicios = Servicio.objects.all()
    return render(request, 'lista_servicios.html', {'servicios': servicios})






# Definir horarios disponibles manualmente como una variable global
horarios_disponibles_globales = [
    '09:30', '10:00', '10:30',
    '11:00', '11:30', '12:00', '12:30',
    '13:00', '13:30', '14:00', '14:30',
    '15:00', '15:30', '16:00', '16:30',
    '17:00', '17:30', '18:00'
]




def crear_solicitud(request):
    servicios_ids = request.GET.get('servicios', '').split(',')
    servicios_ids = [s_id for s_id in servicios_ids if s_id.isdigit()]
    servicios = Servicio.objects.filter(id__in=servicios_ids)
    
    if not servicios.exists():
        messages.error(request, "No se encontraron servicios.")
        return redirect('lista_servicios')

    if request.method == 'POST':
        cliente = request.POST.get('cliente')
        telefono = request.POST.get('telefono')
        fecha_str = request.POST.get('fecha')
        hora_str = request.POST.get('hora')

        if not (cliente and telefono and fecha_str and hora_str):
            return render(request, 'crear_solicitud.html', {
                'servicios': servicios,
                'horarios_disponibles': horarios_disponibles_globales,
            })

        fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
        hora = datetime.strptime(hora_str, '%H:%M').time()
        fecha_hora_inicio = datetime.combine(fecha, hora)

        for servicio in servicios:
            duracion_servicio = servicio.tiempo_estimado
            fecha_hora_fin = fecha_hora_inicio + duracion_servicio


            solicitud = Solicitud(
                cliente=cliente,
                telefono=telefono,
                fecha=fecha,
                hora=fecha_hora_inicio.time(),
                servicio=servicio,
                trabajador=None  # Trabajador asignado más tarde por el superusuario
            )
            solicitud.save()

            # Actualizar fecha_hora_inicio para el próximo servicio
            fecha_hora_inicio = fecha_hora_fin

        messages.success(request, "")

        return redirect('lista_servicios')

    return render(request, 'crear_solicitud.html', {
        'servicios': servicios,
        'horarios_disponibles': horarios_disponibles_globales,
    })





def obtener_horarios_disponibles(request):
    servicios_ids = request.GET.getlist('servicios[]')
    servicios_ids = [s_id for s_id in servicios_ids if s_id.isdigit()]

    if not servicios_ids:
        return JsonResponse({'error': 'No se proporcionaron servicios válidos.'})

    if request.method == 'GET':
        fecha_str = request.GET.get('fecha')
        
        servicios = Servicio.objects.filter(id__in=servicios_ids)

        if not fecha_str or not servicios.exists():
            return JsonResponse({'horarios': []})

        fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()

        duracion_total = timedelta()
        for servicio in servicios:
            duracion_total += servicio.tiempo_estimado

        horarios_disponibles = []

        # Límite de manicure y pedicure por hora
        limite_manicure = 3
        limite_pedicure = 2

       
        trabajadores_disponibles = Trabajador.objects.filter(activo=True).count()

        for hora_str in horarios_disponibles_globales:
            hora = datetime.strptime(hora_str, '%H:%M').time()
            fecha_hora_inicio = datetime.combine(fecha, hora)
            fecha_hora_fin = fecha_hora_inicio + duracion_total

            ocupacion_manicure = 0
            ocupacion_pedicure = 0
            ocupacion_total = 0
            servicios_validos = True


            for solicitud in Solicitud.objects.filter(fecha=fecha, trabajador__activo=True):
                servicio = solicitud.servicio
                hora_ocupada_inicio = datetime.combine(solicitud.fecha, solicitud.hora)
                hora_ocupada_fin = hora_ocupada_inicio + servicio.tiempo_estimado

                if fecha_hora_inicio < hora_ocupada_fin and fecha_hora_fin > hora_ocupada_inicio:
                    ocupacion_total += 1
                    if 'manicure' in servicio.nombre.lower():
                        ocupacion_manicure += 1
                    elif 'pedicure' in servicio.nombre.lower():
                        ocupacion_pedicure += 1

            if ('manicure' in [s.nombre.lower() for s in servicios] and ocupacion_manicure >= limite_manicure) or \
               ('pedicure' in [s.nombre.lower() for s in servicios] and ocupacion_pedicure >= limite_pedicure):
                servicios_validos = False

            # Validación de ocupación general de trabajadores
            if ocupacion_total >= trabajadores_disponibles:
                servicios_validos = False

            # Si los servicios son válidos, añadimos la secuencia de horarios según la disponibilidad
            if servicios_validos:
                hora_actual = fecha_hora_inicio
                secuencia_valida = True
                
                # Validar que la secuencia completa de servicios cabe dentro del horario disponible
                for servicio in servicios:
                    if secuencia_valida:
                        hora_actual_fin = hora_actual + servicio.tiempo_estimado
                        # Revisar si hay conflictos con los trabajadores habilitados en este horario
                        ocupacion_en_hora = 0
                        for solicitud in Solicitud.objects.filter(fecha=fecha, trabajador__activo=True):
                            hora_inicio_conflicto = datetime.combine(solicitud.fecha, solicitud.hora)
                            hora_fin_conflicto = hora_inicio_conflicto + solicitud.servicio.tiempo_estimado
                            if hora_actual < hora_fin_conflicto and hora_actual_fin > hora_inicio_conflicto:
                                ocupacion_en_hora += 1
                        if ocupacion_en_hora >= trabajadores_disponibles:
                            secuencia_valida = False
                        else:
                            hora_actual = hora_actual_fin  # avanzar al siguiente intervalo de servicio

                if secuencia_valida:
                    # Añadir el horario de inicio si la secuencia completa es válida
                    horarios_disponibles.append(fecha_hora_inicio.strftime('%H:%M'))

        horarios_disponibles = sorted(list(set(horarios_disponibles)))

        return JsonResponse({'horarios': horarios_disponibles})

    return render(request, 'crear_solicitud.html', {
        'servicios': servicios,
        'horarios_disponibles': horarios_disponibles,
    })




def toggle_trabajador_activo(request, trabajador_id):
    trabajador = get_object_or_404(Trabajador, id=trabajador_id)
    trabajador.activo = not trabajador.activo  # Cambia el estado
    trabajador.save()
    return redirect('solicitudes_admin')

@login_required
def solicitudes_admin(request):
    if not request.user.is_superuser:  
        return HttpResponseForbidden("No tienes permiso para acceder a esta página.")

    solicitudes = Solicitud.objects.all()  
    trabajadores = Trabajador.objects.all() 
    trabajadores_habilitados = Trabajador.objects.filter(activo=True) 

    context = {
        'solicitudes': solicitudes,
        'trabajadores': trabajadores,
        'trabajadores_habilitados': trabajadores_habilitados
    }
    return render(request, 'solicitudes_admin.html', context)


@login_required
def asignar_trabajador(request, solicitud_id):
    if not request.user.is_superuser:
        return HttpResponseForbidden("No tienes permiso para acceder a esta página.")

    solicitud = get_object_or_404(Solicitud, id=solicitud_id)
    
    if request.method == 'POST':
        trabajador_id = request.POST.get('trabajador')
        
        if trabajador_id:
            trabajador = get_object_or_404(Trabajador, id=trabajador_id)
            solicitud.trabajador = trabajador 
            solicitud.estado = 'En progreso' 
            solicitud.save()  
            
            messages.success(request, 'Trabajador asignado exitosamente.')
        else:
            messages.error(request, 'No se ha seleccionado un trabajador.')
        
        return redirect('solicitudes_admin')

    return redirect('solicitudes_admin') 


def register_superuser(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        password2 = request.POST['password2']

        if password == password2:
            if User.objects.filter(username=username).exists():
                messages.error(request, 'El nombre de usuario ya está en uso')
            else:
                user = User.objects.create_user(username=username, password=password)
                user.is_superuser = True
                user.is_staff = True
                user.save()
                messages.success(request, 'Superusuario registrado correctamente')
                return redirect('login')
        else:
            messages.error(request, 'Las contraseñas no coinciden')

    return render(request, 'register_superuser.html')

@login_required
def registrar_trabajador(request):
    if request.method == 'POST':
        nombre = request.POST['nombre']
        username = request.POST['username']
        password = request.POST['password']
        telefono = request.POST['telefono']

        if User.objects.filter(username=username).exists():
            messages.error(request, 'El nombre de usuario ya está en uso')
        else:
            # Crear usuario
            user = User.objects.create_user(username=username, password=password)
            user.is_staff = True  
            user.save()

            
            trabajador = Trabajador(user=user, nombre=nombre, telefono=telefono)
            trabajador.save()

            messages.success(request, 'Trabajador registrado correctamente')
            return redirect('login')

    return render(request, 'registrar_trabajador.html')

@login_required
def solicitudes_trabajador(request):
    if not request.user.is_staff or request.user.is_superuser:
        return HttpResponseForbidden("No tienes permiso para acceder a esta página.")
    
    
    # Obtener el trabajador vinculado al usuario actual
    try:
        trabajador = Trabajador.objects.get(user=request.user)
        
        solicitudes = Solicitud.objects.filter(trabajador=trabajador)
    except Trabajador.DoesNotExist:
        solicitudes = []  

    return render(request, 'solicitudes_trabajador.html', {'solicitudes': solicitudes, 'trabajadores':trabajador})


def toggle_trabajador_activo(request, trabajador_id):
    # Obtén el trabajador con el ID proporcionado
    trabajador = get_object_or_404(Trabajador, id=trabajador_id)

    # Cambia el estado del trabajador
    trabajador.activo = not trabajador.activo  # Si está activo, se desactiva, y viceversa
    trabajador.save()

    # Redirige de vuelta a la vista de solicitudes
    return redirect('solicitudes_admin')

def custom_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            print(f"Usuario autenticado: {user.username}, is_superuser: {user.is_superuser}, is_staff: {user.is_staff}")

            if user.is_superuser:
                messages.success(request, 'Has iniciado sesión como administrador.')
                return redirect('solicitudes_admin')  
            elif Trabajador.objects.filter(user=user).exists():
                messages.success(request, 'Has iniciado sesión como trabajador.')
                return redirect('solicitudes_trabajador')  
            else:
                messages.success(request, 'Has iniciado sesión con éxito.')
                return redirect('lista_servicios')  
        else:
            messages.error(request, 'Credenciales inválidas. Inténtalo de nuevo.')
            return render(request, 'login.html')
    
    return render(request, 'login.html')


def custom_logout(request):
    logout(request)
    return redirect('login')


#muestra los servicios que le han sido asignados al trabajador
@login_required
def servicios_trabajador(request):
    trabajador = request.user  # El trabajador autenticado
    servicios = Servicio.objects.filter(trabajador=trabajador)  

    
    return render(request, 'trabajador/servicios.html', {'servicios': servicios})

def aceptar_solicitud(request, solicitud_id):
    solicitud = get_object_or_404(Solicitud, id=solicitud_id)
    trabajador = solicitud.trabajador  # Obtén al trabajador asignado a la solicitud
    
    if solicitud.estado in ['En progreso', 'Rechazada', 'Pendiente']:  # Verificamos que la solicitud esté en estado válido
        total = solicitud.servicio.precio  # Precio completo del servicio
        
        # Actualizamos el total a pagar del trabajador
        trabajador.total_pagar += total  # Suma el precio completo al total_pagar
        
        # Calculamos lo que le corresponde al trabajador por este servicio
        monto = solicitud.servicio.precio / 2  # El trabajador gana la mitad del precio del servicio
        
        # Actualizamos el total ganado del trabajador
        trabajador.total_ganado += monto
        trabajador.save()
        
        # Cambiamos el estado de la solicitud a 'Aceptada'
        solicitud.estado = 'Aceptada'
        solicitud.save()
        
        # Mensaje de éxito
        messages.success(request, f"Solicitud aceptada. Total ganado y total a pagar actualizados para {trabajador.nombre}.")
    else:
        # Si la solicitud ya fue aceptada o rechazada, mostramos un error
        messages.error(request, "La solicitud ya ha sido aceptada o rechazada.")
    
    return redirect('solicitudes_trabajador')

@login_required
def rechazar_solicitud(request, solicitud_id):
    solicitud = get_object_or_404(Solicitud, id=solicitud_id)
    solicitud.estado = 'Rechazada'  
    solicitud.save()
    
    messages.error(request, 'Solicitud rechazada.')
    return redirect('solicitudes_trabajador') 


# contabilidad 
def contabilidad(request):
    # Obtener la fecha actual
    hoy = timezone.now().date()
    
    # Calcular total del día
    total_dia = Solicitud.objects.filter(fecha=hoy).aggregate(Sum('servicio__precio'))['servicio__precio__sum'] or 0

    # Calcular total de la semana
    inicio_semana = hoy - timezone.timedelta(days=hoy.weekday())  # Lunes de esta semana
    total_semana = Solicitud.objects.filter(fecha__gte=inicio_semana).aggregate(Sum('servicio__precio'))['servicio__precio__sum'] or 0

    # Calcular total del mes
    inicio_mes = hoy.replace(day=1)  # Primer día del mes
    total_mes = Solicitud.objects.filter(fecha__gte=inicio_mes).aggregate(Sum('servicio__precio'))['servicio__precio__sum'] or 0

    context = {
        'total_dia': total_dia,
        'total_semana': total_semana,
        'total_mes': total_mes,
    }

    return render(request, 'contabilidad.html', context)

@login_required
def guardar_monto_trabajador(request):
    if request.method == "POST":
        # Obtener los datos del formulario
        trabajador_id = request.POST.get("trabajador")
        monto_adicional = request.POST.get("monto_adicional", 0)

        # Buscar el trabajador por ID
        trabajador = get_object_or_404(Trabajador, id=trabajador_id)

        # Convertir monto_adicional a Decimal
        monto_adicional_decimal = Decimal(monto_adicional)

        # Actualizar el campo 'total_pagar' y 'total_ganado' en el trabajador
        trabajador.total_pagar += monto_adicional_decimal
        trabajador.total_ganado += monto_adicional_decimal  # Se asume que el trabajador recibe el monto total
        trabajador.save()

        # Mostrar mensaje de éxito
        messages.success(
            request,
            f"Se añadió un monto de {monto_adicional} a {trabajador.nombre}. "
            f"El total a pagar y lo ganado por el trabajador se han actualizado."
        )

        # Redirigir a la vista de administración de trabajadores o a donde corresponda
        return redirect('solicitudes_admin')  # Ajusta la URL según corresponda

    else:
        return HttpResponseForbidden("Método no permitido.")
    


def crear_solicitud_admin(request):
    servicios_ids = request.GET.get('servicios', '').split(',')
    servicios_ids = [s_id for s_id in servicios_ids if s_id.isdigit()]
    servicios = Servicio.objects.filter(id__in=servicios_ids)

    if not request.user.is_superuser:
        messages.error(request, "No tienes permisos para acceder a esta sección.")
        return redirect('inicio')

    if request.method == 'POST':
        cliente = request.POST.get('cliente')
        telefono = request.POST.get('telefono')
        fecha_str = request.POST.get('fecha')
        hora_str = request.POST.get('hora')
        pago = request.POST.get('pago')
        servicio_id = request.POST.get('servicio')
        trabajador_id = request.POST.get('trabajador')
        precio_total = request.POST.get('precio_total')

        trabajador = Trabajador.objects.get(id=trabajador_id) if trabajador_id else None
        servicio = Servicio.objects.get(id=servicio_id) if servicio_id else None

        if not (cliente and telefono and fecha_str and hora_str and servicio):
            messages.error(request, "Por favor, completa todos los campos obligatorios.")
            return render(request, 'solicitudes_admin.html', {
                'servicios': Servicio.objects.all(),
                'trabajadores': Trabajador.objects.all()
            })

        fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
        hora = datetime.strptime(hora_str, '%H:%M').time()

        Solicitud.objects.create(
            cliente=cliente,
            telefono=telefono,
            fecha=fecha,
            hora=hora,
            pago=pago,
            servicio=servicio,
            trabajador=trabajador,
            estado='Aceptada'
        )

        messages.success(request, "Solicitud creada con éxito.")
        return redirect('solicitudes_admin')

    else:
        return render(request, 'solicitudes_admin.html', {
            'servicios': Servicio.objects.all(),
            'trabajadores': Trabajador.objects.all()
        })




def cargar_servicios_admin(request):
    servicios_ids = request.GET.get('servicios', '').split(',')
    servicios_ids = [s_id for s_id in servicios_ids if s_id.isdigit()]
    servicios = Servicio.objects.filter(id__in=servicios_ids)



