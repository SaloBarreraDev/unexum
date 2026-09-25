from kivymd.app import MDApp
from kivy.uix.screenmanager import Screen
from kivymd.uix.menu import MDDropdownMenu
from kivy.metrics import dp
from kivy.properties import (
    StringProperty,
    ObjectProperty,
    ColorProperty,
)
from kivy.utils import platform
from ..utils.secrets import REWARDED
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

class Repositorio(Screen):
    materia = StringProperty("")
    codigo_materia = StringProperty("")
    nro_parciales = ObjectProperty(0)
    nro_libros = ObjectProperty(0)
    nro_apuntes = ObjectProperty(0)
    nro_guias_teoricas = ObjectProperty(0)
    nro_guias_ejercicios = ObjectProperty(0)
    nro_otros = ObjectProperty(0)
    email_verification = False
    nombre_usuario = ""

class Listado(Screen):
    materia = StringProperty("")
    categoria = StringProperty("")
    unidad = StringProperty("Todas")

class Upload(Screen):
    codigo_materia = ""
    materia = StringProperty("---")
    ruta = ""
    nombre_archivo = StringProperty("---")
    categoria = StringProperty("---")
    tipo = StringProperty("---")
    extension = ""
    peso_documento = ObjectProperty(0)
    unidad = StringProperty("Todas")

    def __init__(self, **kwargs):
        menu_items_categorias = menu_items_appbar = [
            {
                "text": "Parciales y prácticas",
                "on_release": lambda x="Parciales y prácticas": self.seleccionar_categoria(x),
            },
            {
                "text": "Libros y documentos",
                "on_release": lambda x="Libros y documentos": self.seleccionar_categoria(x),
            },
            {
                "text": "Apuntes y notas",
                "on_release": lambda x="Apuntes y notas": self.seleccionar_categoria(x),
            },
            {
                "text": "Guías Teóricas",
                "on_release": lambda x="Guías Teóricas": self.seleccionar_categoria(x),
            },
            {
                "text": "Guías de ejercicios",
                "on_release": lambda x="Guías de ejercicios": self.seleccionar_categoria(x),
            },
            {
                "text": "Otros",
                "on_release": lambda x="Otros": self.seleccionar_categoria(x),
            },
        ]
        self.menu_categorias = MDDropdownMenu(
            caller=None, items=menu_items_categorias, position = "bottom", max_height = dp(200)
        )
        super(Upload, self).__init__(**kwargs)

    def abrir_menu_categoria(self, obj):
        if not self.menu_categorias.caller:
            self.menu_categorias.caller = obj
        self.menu_categorias.open()

    def seleccionar_categoria(self, categoria):
        self.menu_categorias.dismiss()
        self.categoria = categoria

    def seleccionar_unidad(self, unidad):
        self.unidad = unidad


