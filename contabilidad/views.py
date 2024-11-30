from django.shortcuts import render
from .models import Pago, Trabajador, Servicio, Inventario, RegistroFinanciero
from spa.models import Solicitud
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404, get_list_or_404
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from datetime import date
from decimal import Decimal
from django.db.models import Sum, Count
from datetime import datetime, timedelta
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from .models import PagoHistorial

def resumen_contable(request):
    trabajadores = Trabajador.objects.all()

    data = []

    for trabajador in trabajadores:
        # Filtramos las solicitudes aceptadas para cada trabajador
        solicitudes_trabajador = Solicitud.objects.filter(trabajador=trabajador, estado='Aceptada')
        
        # Calcular total de servicios (sumar los precios de los servicios realizados)
        total_servicios = sum(solicitud.servicio.precio for solicitud in solicitudes_trabajador)

        # Calcular el total a pagar (este ya se guarda en el modelo Trabajador)
        total_pagar = trabajador.total_pagar
        total_adelantos = trabajador.total_adelantos
        total = trabajador.total_pagar

        # Almacenar los datos para pasar al template
        data.append({
            'trabajador': trabajador,
            'total_servicios': total_servicios,
            'total_pago': trabajador.total_ganado,  # Esto ya se guarda en el modelo, no es necesario recalcularlo
            'lo_que_corresponde': total_pagar,  # Mostramos el total a pagar calculado previamente
            'adelantos':total_adelantos,
            'total':total
        })

    return render(request, 'resumen_contable.html', {'data': data})




""" def pagar_trabajador(request, trabajador_id):
    trabajador = get_object_or_404(Trabajador, id=trabajador_id)

    # Reiniciar totales del trabajador
    trabajador.total_adelantos = 0
    trabajador.total_ganado = 0  
    trabajador.save()

    return redirect('resumen_contable')  # Redirige al resumen contable """


def servicios_trabajador(request, trabajador_id):
    trabajador = Trabajador.objects.get(id=trabajador_id)
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')

    servicios = Servicio.objects.filter(trabajador=trabajador, fecha__range=[fecha_inicio, fecha_fin])

    context = {
        'trabajador': trabajador,
        'servicios': servicios
    }

    return render(request, 'servicios_trabajador.html', context)


def inventario(request):
    inventarios = Inventario.objects.all()

    context = {
        'inventarios': inventarios
    }

    return render(request, 'inventario.html', context)

def adelanto_trabajador(request):
    if request.method == "POST":
        trabajador_id = request.POST.get("trabajador_id")
        monto_adelanto = Decimal(request.POST.get("monto_adelanto"))
        
        trabajador = Trabajador.objects.get(id=trabajador_id)
        total_pago_actual = trabajador.total_ganado
        
        # Validar que el adelanto no sea mayor al total a pagar
        if monto_adelanto <= total_pago_actual:
            # Actualizar el total de adelantos
            trabajador.total_adelantos += monto_adelanto
            trabajador.total_ganado -= monto_adelanto  # Reducir lo que queda por pagar
            trabajador.save()

            # Registrar el pago (si tienes un modelo de pago)
            Pago.objects.create(
                trabajador=trabajador,
                monto=monto_adelanto,
                tipo='adelanto'  # O algún campo que indique que es un adelanto
            )

            messages.success(request, "Adelanto registrado exitosamente.")
        else:
            messages.error(request, "El adelanto no puede ser mayor al total a pagar.")

        return redirect("resumen_contable")
    
def servicios_por_trabajador_y_dia(request):
    # Obtener la lista de trabajadores
    trabajadores = Trabajador.objects.filter(activo=True)

    # Obtener datos del formulario
    trabajador_id = request.GET.get('trabajador')  # ID del trabajador seleccionado
    fecha = request.GET.get('fecha')  # Fecha seleccionada

    # Inicializar variables para los resultados
    servicios_realizados = []
    total_generado = 0

    # Si se seleccionó un trabajador y una fecha
    if trabajador_id and fecha:
        # Convertir fecha en objeto datetime
        fecha_obj = datetime.strptime(fecha, '%Y-%m-%d').date()

        # Filtrar las solicitudes realizadas por el trabajador y en la fecha seleccionada
        solicitudes = Solicitud.objects.filter(
            trabajador_id=trabajador_id,
            fecha=fecha_obj,
            estado='Aceptada'
        )

        # Obtener datos de los servicios
        servicios_realizados = [
            {
                'servicio': solicitud.servicio.nombre,
                'precio': solicitud.servicio.precio,
                'hora': solicitud.hora,
                'precio_total': solicitud.precio_total
            }
            for solicitud in solicitudes
        ]

        
        # Calcular el total generado
        total_generado = sum(solicitud.servicio.precio + (solicitud.precio_total) for solicitud in solicitudes)

    # Contexto para la plantilla
    context = {
        'trabajadores': trabajadores,
        'servicios_realizados': servicios_realizados,
        'total_generado': total_generado,
        'trabajador_id': int(trabajador_id) if trabajador_id else None,
        'fecha': fecha,
    }

    return render(request, 'servicios_por_trabajador_y_dia.html', context)


def resumen_financiero(request):
    hoy = date.today()
    inicio_semana = hoy - timedelta(days=hoy.weekday())
    inicio_mes = hoy.replace(day=1)

    # Calcular totales
    ingresos_dia = RegistroFinanciero.objects.filter(fecha=hoy, tipo='ingreso').aggregate(Sum('monto'))['monto__sum'] or 0
    egresos_dia = RegistroFinanciero.objects.filter(fecha=hoy, tipo='egreso').aggregate(Sum('monto'))['monto__sum'] or 0

    ingresos_semana = RegistroFinanciero.objects.filter(fecha__gte=inicio_semana, tipo='ingreso').aggregate(Sum('monto'))['monto__sum'] or 0
    egresos_semana = RegistroFinanciero.objects.filter(fecha__gte=inicio_semana, tipo='egreso').aggregate(Sum('monto'))['monto__sum'] or 0

    ingresos_mes = RegistroFinanciero.objects.filter(fecha__gte=inicio_mes, tipo='ingreso').aggregate(Sum('monto'))['monto__sum'] or 0
    egresos_mes = RegistroFinanciero.objects.filter(fecha__gte=inicio_mes, tipo='egreso').aggregate(Sum('monto'))['monto__sum'] or 0

    # Totales en caja
    caja_dia = ingresos_dia - egresos_dia
    caja_semana = ingresos_semana - egresos_semana
    caja_mes = ingresos_mes - egresos_mes

    context = {
        'ingresos_dia': ingresos_dia,
        'egresos_dia': egresos_dia,
        'caja_dia': caja_dia,
        'ingresos_semana': ingresos_semana,
        'egresos_semana': egresos_semana,
        'caja_semana': caja_semana,
        'ingresos_mes': ingresos_mes,
        'egresos_mes': egresos_mes,
        'caja_mes': caja_mes,
    }

    return render(request, 'resumen_financiero.html', context)





def historial_servicios(request):
    # Variables para manejar los resultados
    historial = []
    total_servicios = 0
    total_para_trabajadores = 0
    total_pago_efectivo = 0
    total_pago_nequi = 0
    paguito=0
    total_por_trabajador = {}  # Diccionario para almacenar el total por trabajador

    # Obtener todos los trabajadores activos
    trabajadores = Trabajador.objects.all()

    # Validar si se han enviado las fechas
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')

    if fecha_inicio and fecha_fin:
        try:
            # Convertir las fechas a objetos datetime
            fecha_inicio = datetime.strptime(fecha_inicio, '%Y-%m-%d')
            fecha_fin = datetime.strptime(fecha_fin, '%Y-%m-%d')

            # Filtrar las solicitudes en el rango de fechas
            solicitudes = Solicitud.objects.filter(fecha__range=(fecha_inicio, fecha_fin), estado='Aceptada')

            # Procesar los datos
            for solicitud in solicitudes:
                trabajador = solicitud.trabajador  
                servicio = solicitud.servicio
                precio_total = solicitud.precio_total
                corresponde_trabajador = (servicio.precio / 2) + (precio_total / 2)
                suma = servicio.precio + precio_total

                # Agregar al historial
                historial.append({
                    'trabajador': trabajador,
                    'servicio': servicio,
                    'fecha': solicitud.fecha,
                    'corresponde_trabajador': corresponde_trabajador,
                    'solicitud': solicitud,
                    'precio_total': precio_total,
                    'tipo': 'Servicio',
                    'suma': suma,
                })

                # Obtener pagos específicos del trabajador
                pagos = Pago.objects.filter(tipo__in=['adelanto', 'pago'], trabajador=trabajador)

                # Sumar los pagos realizados
                pagos_totales = pagos.aggregate(total=Sum('monto'))['total'] or 0

                # Acumulando el total que corresponde a cada trabajador, restando los pagos ya realizados
                total_trabajador_con_pago = corresponde_trabajador - pagos_totales
                total_servicios += suma /2   # Restar los pagos ya realizados

                # Actualizar el total para cada trabajador en el diccionario
                if trabajador.id not in total_por_trabajador:
                    total_por_trabajador[trabajador.id] = 0
                total_por_trabajador[trabajador.id] += total_trabajador_con_pago

                # Contabilizar según el método de pago
                if solicitud.pago == 'efectivo':
                    total_pago_efectivo += suma
                elif solicitud.pago == 'nequi':
                    total_pago_nequi += suma
                
            paguito = total_pago_nequi + total_pago_efectivo
            print('pago total',paguito)                
             

        except ValueError:
            # Manejar error de formato de fecha
            return render(request, 'historial_servicios.html', {
                'error': 'Las fechas ingresadas no son válidas.'
            })
        
        
    trabajadores_info = []
    total_para_trabajadores = 0  # Acumulador para el total a pagar de todos los trabajadores

    for trabajador in trabajadores:
        # Reiniciar las variables para cada trabajador
        total_ganado_trabajador = trabajador.total_ganado

        # Calcular el total que queda por pagar (total ganado - total adelantos)
        total_por_trabajador = total_ganado_trabajador

        # Sumar el total a pagar de este trabajador al acumulador general
        total_para_trabajadores += total_por_trabajador  # Acumulando el total, no sobrescribiendo

            

        # Pasar los campos de total_ganado, total_adelantos, total_pagar a los trabajadores
        
    trabajadores_info = []
    for trabajador in trabajadores:
        trabajadores_info.append({
            'nombre': trabajador.nombre,
            'total_ganado': trabajador.total_ganado,
            'total_adelantos': trabajador.total_adelantos,
            'total_pagar': trabajador.total_pagar,
        })

    return render(request, 'historial_servicios.html', {
        'historial': historial,
        'total_servicios': total_servicios,
        'total_para_trabajadores': total_para_trabajadores,
        'total_pago_efectivo': total_pago_efectivo,
        'total_pago_nequi': total_pago_nequi,
        'trabajadores_info': trabajadores_info,  # Pasar los campos adicionales de los trabajadores
        'paguito':paguito})






@login_required
def add_monto_adicional(request):
    if request.method == "POST":
        solicitud_id = request.POST.get("solicitud_id")
        monto_adicional = request.POST.get("monto_adicional", 0)

        solicitud = get_object_or_404(Solicitud, id=solicitud_id)
        trabajador = solicitud.trabajador  

        # Convertir monto_adicional a Decimal antes de sumarlo
        monto_adicional_decimal = Decimal(monto_adicional)

        # Actualizar el precio_total de la solicitud
        solicitud.precio_total += monto_adicional_decimal
        solicitud.save()

        # Si la solicitud tiene un trabajador asignado, actualizamos su total_ganado
        if trabajador:
            trabajador.total_ganado += (monto_adicional_decimal/2)
            trabajador.total_pagar += monto_adicional_decimal
            trabajador.save()

        messages.success(
            request,
            f"Se añadió un monto adicional de {monto_adicional} a la solicitud de {solicitud.cliente}. "
            f"El trabajador {trabajador.nombre} también fue actualizado." if trabajador else ""
        )
        return redirect('solicitudes_admin')
    else:
        return HttpResponseForbidden("Método no permitido.")
    
    
def registrar_adelanto(request):
    if request.method == "POST":
        trabajador_id = request.POST.get("trabajador_id")
        monto_adelanto = Decimal(request.POST.get("monto_adelanto"))

        trabajador = get_object_or_404(Trabajador, id=trabajador_id)

        # Registrar el adelanto en PagoHistorial
        PagoHistorial.objects.create(
            trabajador=trabajador,
            monto=monto_adelanto,
            tipo="adelanto",
            descripcion=""
        )

        # Actualizar los valores en el modelo Trabajador
        trabajador.total_adelantos += monto_adelanto
        trabajador.actualizar_total_pagar()

        messages.success(request, f"Se registró un adelanto de ${monto_adelanto} para {trabajador.nombre}.")
        return redirect("resumen_contable")
    


    

def pagar_trabajador(request, trabajador_id):
    trabajador = get_object_or_404(Trabajador, id=trabajador_id)


    if trabajador.total_pagar > 0:
        # Registrar el pago total en la tabla Pago
        Pago.objects.create(
            trabajador=trabajador,
            monto=trabajador.total_ganado,
            tipo="pago",  # Indicamos que es un pago total
            descripcion=""
        )

        # Resetear los valores de los campos del trabajador
        trabajador.total_ganado = 0
        trabajador.total_adelantos = 0
        trabajador.total_pagar = 0
        trabajador.save()

        messages.success(request, f"Se realizó el pago total para {trabajador.nombre}.")
    else:
        messages.warning(request, f"No hay monto pendiente para pagar a {trabajador.nombre}.")

    return redirect("resumen_contable")


def cambiar_modo_pago(request):
    if request.method == 'POST':
        solicitud_id = request.POST.get('solicitud_id')
        solicitud = get_object_or_404(Solicitud, id=solicitud_id)
        
        # Cambiar el método de pago
        if solicitud.pago == 'efectivo':
            solicitud.pago = 'nequi'
        else:
            solicitud.pago = 'efectivo'
        solicitud.save()

        messages.success(request, f"El método de pago se cambió a {solicitud.pago}.")
        return redirect('solicitudes_admin') 