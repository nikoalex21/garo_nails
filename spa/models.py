from django.db import models
from django.contrib.auth.models import User

class Servicio(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField()
    precio = models.DecimalField(max_digits=10, decimal_places=0)
    tiempo_estimado = models.DurationField()

    def __str__(self):
        return self.nombre

class Trabajador(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    nombre = models.CharField(max_length=100)
    telefono = models.CharField(max_length=15)
    servicios = models.ManyToManyField(Servicio, blank=True)
    total_ganado = models.DecimalField(max_digits=10, decimal_places=0, default=0)
    total_adelantos = models.DecimalField(max_digits=10, decimal_places=0, default=0)
    total_pagar = models.DecimalField(max_digits=10, decimal_places=0, default=0)  # Nuevo campo para total a pagar
    activo = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre

    def actualizar_total_pagar(self):
        """Método para actualizar el total a pagar basado en el total ganado y los adelantos."""
        self.total_pagar = self.total_ganado - self.total_adelantos
        self.save()
    
    

class Solicitud(models.Model):
    cliente = models.CharField(max_length=100)
    telefono = models.CharField(max_length=15)
    fecha = models.DateField()
    hora = models.TimeField()
    pago = models.CharField(max_length=20, default='efectivo') 
    servicio = models.ForeignKey(Servicio, on_delete=models.CASCADE)
    estado = models.CharField(max_length=20, default='Pendiente') 
    trabajador = models.ForeignKey(Trabajador, on_delete=models.SET_NULL, null=True)
    precio_total = models.DecimalField(max_digits=10, decimal_places=0, default=0)

    def __str__(self):
        return f'Solicitud de {self.cliente} para {self.servicio.nombre}'

