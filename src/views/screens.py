from kivymd.app import MDApp
from kivy.uix.screenmanager import Screen
from kivy.properties import (
    StringProperty,
    ObjectProperty,
    ColorProperty,
)
from kivy.utils import platform
# Pantallas
class Acerca(Screen):
    pass

class DescargoResponsabilidad(Screen):
    pass

class Colaboradores(Screen):
    pass

class Licencias(Screen):
    pass

class GenerarHorario(Screen):
    numero_horario = ObjectProperty(0)
    max_horarios = ObjectProperty(0)

class Configuracion(Screen):
    tiempo_espera = ObjectProperty("Optimizada")
    tema = ObjectProperty("")
    primer_acceso = True

    def on_enter(self, *args):
        if platform == "android" and self.primer_acceso:
            self.primer_acceso = False
            app = MDApp.get_running_app()
            app.admob.load_rewarded(REWARDED)

class Login(Screen):
    def on_pre_enter(self, *args):
        app = MDApp.get_running_app()
        app.widget_principal.menu_especialidad.caller = self.ids["BotonEspecialidad"]
        app.widget_principal.menu_mencion.caller = self.ids["BotonMencion"]
        app.widget_principal.menu_mencion.open()
        app.widget_principal.menu_mencion.dismiss()
        app.widget_principal.menu_especialidad.open()
        app.widget_principal.menu_especialidad.dismiss()

class Horario(Screen):
    texto_lapso_academico = StringProperty("---")
    texto_fecha_actualizacion = StringProperty("---")

class Evaluaciones(Screen):
    materia = None
    nombre_materia = StringProperty("")
    nota_total = ObjectProperty(0)
    nota_final = ObjectProperty(0)
    ponderacion_total = ObjectProperty(0)
    nota_pasar = ObjectProperty(0)
    nota_sustituir = ObjectProperty(0)
    media_porcentual = ObjectProperty(0)
    media = ObjectProperty(0)
    aporte = ObjectProperty(0)
    tema = ObjectProperty()
    color_chip = ColorProperty()

class Estadisticas(Screen):
    tema = ObjectProperty()
