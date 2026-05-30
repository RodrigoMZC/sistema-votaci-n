from django.core.management.base import BaseCommand
from accounts.models import CustomUser

class Command(BaseCommand):
    help = 'Crea usuarios iniciales de prueba'

    def handle(self, *args, **kwargs):
        if not CustomUser.objects.filter(username='admin').exists():
            CustomUser.objects.create_superuser(
                username='admin',
                email='admin@votaciones.com',
                password='Admin1234!'
            )
            self.stdout.write(self.style.SUCCESS('Superusuario "admin" creado exitosamente.'))
        else:
            self.stdout.write(self.style.WARNING('El superusuario "admin" ya existe.'))

        if not CustomUser.objects.filter(username='usuario').exists():
            CustomUser.objects.create_user(
                username='usuario',
                email='usuario@votaciones.com',
                password='Usuario1234!',
                bio='Usuario de prueba',
            )
            self.stdout.write(self.style.SUCCESS('✓ Usuario normal creado'))
        else:
            self.stdout.write(self.style.WARNING('— usuario ya existe, se omite'))
            
        self.stdout.write(self.style.SUCCESS('\nSeeder completado.'))
        self.stdout.write('Admin    → usuario: admin     / contraseña: Admin1234!')
        self.stdout.write('Usuario  → usuario: usuario   / contraseña: Usuario1234!')