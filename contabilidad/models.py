from django.db import models
from spa.models import Trabajador, Servicio,Solicitud  # Asumiendo que Trabajador está en la app 'spa'
from datetime import datetime

class Pago(models.Model):
    trabajador = models.ForeignKey(Trabajador, on_delete=models.CASCADE)
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    tipo = models.CharField(max_length=10, choices=[('pago', 'Pago'), ('adelanto', 'Adelanto')])
    fecha = models.DateField(auto_now_add=True)
    descripcion = models.CharField(max_length=255, blank=True, null=True)


    def __str__(self):
        return f'{self.trabajador.nombre} - {self.tipo} - {self.monto}'
    
class Inventario(models.Model):
    fecha = models.DateField()
    total_servicios = models.IntegerField(default=0)
    total_pago_trabajadores = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return f'Inventario {self.fecha}'
    
class RegistroFinanciero(models.Model):
    fecha = models.DateField(default=datetime.now)  # Fecha del registro
    tipo = models.CharField(max_length=10, choices=[('ingreso', 'Ingreso'), ('egreso', 'Egreso')])  # Tipo de registro
    monto = models.DecimalField(max_digits=10, decimal_places=2)  # Monto del ingreso o egreso
    descripcion = models.TextField(null=True, blank=True)  # Descripción opcional del registro

    def __str__(self):
        return f"{self.tipo.capitalize()} - {self.monto} ({self.fecha})"
    
class PagoHistorial(models.Model):
    trabajador = models.ForeignKey(Trabajador, on_delete=models.CASCADE)
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    tipo = models.CharField(max_length=10, choices=[('total', 'Pago Total'), ('adelanto', 'Adelanto')])
    fecha = models.DateField(auto_now_add=True)
    descripcion = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f'{self.trabajador.nombre} - {self.tipo} - ${self.monto} ({self.fecha})'