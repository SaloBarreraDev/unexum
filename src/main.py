import os
os.environ["A4K_BACKEND"] = "pyjnius"
from os.path import exists, join, dirname, abspath
import shutil
import zipfile
import datetime
from fpdf import FPDF
from PIL import Image as Imagepillow
import json
import threading
import random
import copy
import certifi
from itertools import product

from kivy.logger import Logger
from kivy.config import Config
import asynckivy as ak
from kivy.core.window import Window
from kivy.core.clipboard import Clipboard
from kivy.utils import platform
try:
    from android.runnable import run_on_ui_thread  # type: ignore
except ImportError:
    def run_on_ui_thread(func):
        return func
from src.android_permissions import AndroidPermissions
from kivymd.app import MDApp
import matplotlib.pyplot as plt
import kivy_matplotlib_widget
from kivy.network.urlrequest import UrlRequest
from kivymd.uix.menu import MDDropdownMenu
from kivy.metrics import dp
from kivy.uix.image import Image
from kivy.uix.screenmanager import ScreenManager, SlideTransition, NoTransition
from kivy.properties import (StringProperty, ObjectProperty, BooleanProperty,
    ColorProperty)
from kivymd.uix.navigationbar import MDNavigationBar, MDNavigationItem
from kivymd.uix.selectioncontrol import MDCheckbox
from kivymd.uix.textfield import MDTextField
from kivymd.uix.dialog import (
    MDDialog,
    MDDialogSupportingText,
    MDDialogHeadlineText,
    MDDialogButtonContainer,
    MDDialogContentContainer,
    MDDialogIcon,
)
from kivy.clock import Clock, mainthread
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.divider import MDDivider
from kivymd.uix.button import MDButton, MDButtonText, MDIconButton, MDButtonIcon
from kivymd.uix.widget import Widget
from kivymd.uix.snackbar import MDSnackbar, MDSnackbarText, MDSnackbarSupportingText
from src.data_manager import cargar_datos, migrar_datos
from kivymd.uix.label import MDLabel
from kivymd.uix.relativelayout import MDRelativeLayout
from kivy.animation import Animation
from src.expansionpanel import FMDExpansionPanel
from kivy.resources import resource_add_path

#Importaciones de modulos
from src.utils import (get_height_of_bar, set_status_bar_color, 
    set_status_bar_icons_dark, set_navigation_bar_black, VERSION,
    URL_BASE_DATOS_HORARIO, URL_VERSION_HORARIO, interpolar_nota)
from src.utils.secrets import REWARDED, INTERSTITIAL
from src.views.screens import (Acerca, DescargoResponsabilidad, Colaboradores,
    Licencias, GenerarHorario, Configuracion, Login, Horario, Evaluaciones,
    Estadisticas)
from src.views.custom_widgets import (BoxLayoutElevated, CustomMDScrollView, BoxConRipple, BoxConRippleIndice,
    LabelListaIndice, CampoTextoListaIndice, BoxConRipplePensum, LabelListaPensum,
    CheckBoxPensum, CampoTextoHorario, SelectableRecycleBoxLayout, SelectableLabel, RV,
    SelectableLabelHorario, RVHorario, BoxConRippleInicio, ExpansionPanelItem, TrailingPressedIconButton,
    Seccion)
from src.models import Materia, Evaluacion
Config.set('kivy', 'log_level', 'info')
Config.set("graphics", "maxfps", "120")
Window.softinput_mode = "below_target"
RUTA_ARCHIVOS = None

if platform == "android":
    Config.remove_option("input", "mouse")
    from androidstorage4kivy import SharedStorage, Chooser
    from src.admob4kivy import AdmobManager
    from android import mActivity  # type: ignore
    context = mActivity.getApplicationContext()
    result = context.getExternalFilesDir(None)
    if result:
        RUTA_ARCHIVOS = str(result.toString())
elif platform == "win":
    Window.size = (360, 640)
    # Window.size=(640,360)
    RUTA_ARCHIVOS = "."

RUTA_DATOS = join(RUTA_ARCHIVOS, "datos_usuario")
os.makedirs(RUTA_DATOS, exist_ok = True)
matplotlib_cache_dir = join(RUTA_DATOS, "matplotlib_cache")
os.makedirs(matplotlib_cache_dir, exist_ok=True)
os.environ["MPLCONFIGDIR"] = matplotlib_cache_dir

#Obtener ruta de la carpepta Assets
# 1. Obtiene la ruta donde está este archivo (src/main.py)
DIR_ACTUAL = dirname(abspath(__file__))

# 2. Sube un nivel para llegar a la raíz del proyecto (porque src está dentro de la raíz)
DIR_RAIZ = dirname(DIR_ACTUAL)

# 3. Define la ruta a la carpeta assets
RUTA_ASSETS = join(DIR_RAIZ, 'assets')
resource_add_path(RUTA_ASSETS)

def run_in_thread(fn):
    def run(*k, **kw):
        t = threading.Thread(target=fn, args=k, kwargs=kw, daemon=True)
        t.start()
        return t
    return run

# Decoradores para autoguardado
def auto_save_materias(func):
    def wrapper(self, *args, **kwargs):
        result = func(self, *args, **kwargs)
        # Llamamos a guardar en un hilo para no congelar la UI
        threading.Thread(target=self.guardar_datos, args=(self.get_materias(),), daemon=True).start()
        return result
    return wrapper

def auto_save_usuario(func):
    def wrapper(self, *args, **kwargs):
        result = func(self, *args, **kwargs)
        threading.Thread(target=self.guardar_datos_usuario, daemon=True).start()
        return result
    return wrapper

def auto_save_horario(func):
    def wrapper(self, *args, **kwargs):
        result = func(self, *args, **kwargs)
        if self.datos_usuario_horario:
            threading.Thread(target=self.guardar_datos_horario, daemon=True).start()
        return result
    return wrapper

class Widget_Principal(ScreenManager):
    # Primer acceso (Requiere login)
    requiere_login = False
    # Pantalla activa
    pensum_active = BooleanProperty(False)
    inicio_active = BooleanProperty(True)
    notas_active = BooleanProperty(False)
    horario_active = BooleanProperty(False)
    # Verificar si ya se han creado los widgets
    activado = True
    cargar_indice = True
    activado_pensum = True
    cargar_pensum = True
    activado_bloques_horario = True
    # Retraso cambio de pantalla
    navegacion_desactivada = BooleanProperty(False)
    # Campos de texto login
    texto_nombre = StringProperty("")
    texto_especialidad = StringProperty("")
    texto_mencion = StringProperty("")
    texto_mencion_label = StringProperty("")
    indice_academico = ObjectProperty()
    icono_especialidad = StringProperty("arrow-right-bold")
    icono_mencion = StringProperty("arrow-right-bold")
    # Para saltar al siguiente campos al dar enter
    lista_campos = []
    # Widgets en notas
    widgets_lista_notas = []
    numero_widget_notas = 0
    # Widgets en pensum
    diccionario_widgets_pensum = {}
    diccionario_checkboxs_pensum = {}
    # Para mostrar información materias
    ejecucion = True
    # Mostrar en widgets
    unidades_aprobadas = ObjectProperty()
    unidades_totales = ObjectProperty()
    materias_aprobadas = ObjectProperty()
    materias_totales = ObjectProperty(0)
    porcentaje_aprobadas = ObjectProperty(0)
    porcentaje_uc_aprobadas = ObjectProperty(0)
    semestre_actual = StringProperty()
    mencion_honorifica = StringProperty("-")
    unidades_para_inscribir = ObjectProperty()
    unidades_inscritas = ObjectProperty()
    lista_materias_para_inscribir = []
    old_lista_materias_para_inscribir = []
    # Verificacion de materias de basico aprobadas
    materias_basico = False
    # Diccionario para seleccionar electivas
    contador_electivas = 0
    diccionario_checkboxs_electivas = {}
    # Velocidad de carga de Widgets
    tiempo_espera = None
    texto_tiempo_espera = StringProperty("Optimizada")
    # Materias para inscribir en inicio
    lista_materias_inicio_inscribir = []
    lista_materias_inicio_inscritas = []
    bloques_horario = []
    labels_horario_materias = []
    bloques_horario_materias = []
    # Número de horario
    numero_horario = ObjectProperty(0)
    max_horarios = 0
    # colores al presionar boton
    cambiar_colores = None
    color = None
    # Guias primera vez
    guia_inicio = True
    guia_indice = True
    guia_pensum = True
    guia_horario = True
    # Colores tema
    tema = StringProperty()
    tema_ingles = "Dark"
    borde_letra_grueso = ObjectProperty()
    borde_letra_fino = ObjectProperty()
    color_fondo = ColorProperty()
    color_fondo_claro = ColorProperty()
    color_fondo_mas_claro = ColorProperty()
    LETRA_INTERMEDIA = StringProperty()
    LETRA_FUERTE = StringProperty()
    # Colores
    NARANJA_CLARO = ColorProperty([0.855, 0.388, 0.016, 1])
    NARANJA_OSCURO = ColorProperty([0.678, 0.302, 0, 1])
    AZUL_MAS_CLARO = ColorProperty([0.216, 0.349, 0.643, 1])
    AZUL_CLARO = ColorProperty([0.067, 0.227, 0.573, 1])
    AZUL_OSCURO = ColorProperty([0.035, 0.169, 0.455])
    VERDE = ColorProperty([0.027, 0.549, 0, 1])
    AMARILLO = ColorProperty([0.855, 0.647, 0.125, 1])
    CYAN = ColorProperty([0.08, 0.518, 0.502, 1])
    # rosa
    mari = 0
    # Base datos horario
    datos_usuario_horario = {}
    panel_activado = True
    version_local_horario = 0 
    base_datos_horario = None

    # Arranque de la app
    def __init__(self, **kwargs):
        super(Widget_Principal, self).__init__(**kwargs)

        menu_items_especialidad = [
            {
                "text": "Ing. Eléctrica",
                "leading_icon": "transmission-tower",
                "on_release": lambda x="Ing. Eléctrica": self.set_texto_especialidad(x),
            },
            {
                "text": "Ing. Electrónica",
                "leading_icon": "chip",
                "on_release": lambda x="Ing. Electrónica": self.set_texto_especialidad(
                    x
                ),
            },
            {
                "text": "Ing. Industrial",
                "leading_icon": "factory",
                "on_release": lambda x="Ing. Industrial": self.set_texto_especialidad(
                    x
                ),
            },
            {
                "text": "Ing. Mecánica",
                "leading_icon": "cogs",
                "on_release": lambda x="Ing. Mecánica": self.set_texto_especialidad(x),
            },
            {
                "text": "Ing. Metalúrgica",
                "leading_icon": "anvil",
                "on_release": lambda x="Ing. Metalúrgica": self.set_texto_especialidad(
                    x
                ),
            },
            {
                "text": "Ing. Química",
                "leading_icon": "test-tube",
                "on_release": lambda x="Ing. Química": self.set_texto_especialidad(x),
            },
        ]
        self.menu_especialidad = MDDropdownMenu(
            caller=None,
            items=menu_items_especialidad,
            position="bottom",
        )

        menu_items_mencion = [
            {
                "text": "Computación",
                "leading_icon": "laptop",
                "on_release": lambda x="Computación": self.set_texto_mencion(x),
            },
            {
                "text": "Comunicaciones",
                "leading_icon": "signal-variant",
                "on_release": lambda x="Comunicaciones": self.set_texto_mencion(x),
            },
            {
                "text": "Control",
                "leading_icon": "sine-wave",
                "on_release": lambda x="Control": self.set_texto_mencion(x),
            },
        ]
        self.menu_mencion = MDDropdownMenu(
            caller=None, items=menu_items_mencion, position="bottom"
        )

        menu_items_appbar = [
            {
                "text": "Configuración",
                "leading_icon": "wrench",
                "on_release": lambda x="Configuracion": self.boton_appbar(x),
            },
            {
                "text": "Acerca de esta app",
                "leading_icon": "information",
                "on_release": lambda x="Acerca": self.boton_appbar(x),
            },
        ]
        self.menu_appbar = MDDropdownMenu(
            caller=self.ids.BotonAppBar, items=menu_items_appbar
        )

        menu_items_velocidad_carga = [
            {"text": "Rápida", "on_release": lambda x=0.1: self.velocidad_carga(x)},
            {"text": "Optimizada", "on_release": lambda x=0.2: self.velocidad_carga(x)},
        ]
        self.menu_velocidad_carga = MDDropdownMenu(
            caller=None, items=menu_items_velocidad_carga, position="bottom"
        )

        Window.bind(on_keyboard=self.back_press)

    def get_materias(self, force_reload=False):
        if force_reload or self.materias_cache is None:
            self.materias_cache = cargar_datos(self)  # Usa la función importada
            self.materias_dict = {m.codigo: m for m in self.materias_cache}
            # Invalida electivas porque cargar_datos también resetea Materia.electivas
            self.electivas_cache = None
            self.electivas_dict = {}
        return self.materias_cache

    def get_electivas(self, force_reload=False):
        if force_reload or self.electivas_cache is None:
            self.electivas_cache = self._cargar_electivas_desde_archivo()
            self.electivas_dict = {m.codigo: m for m in self.electivas_cache}
        return self.electivas_cache

    def _cargar_electivas_desde_archivo(self):
        especialidad_to_archivo = {"Ing. Industrial": "industrial",
        "Ing. Eléctrica": "electrica",
        "Ing. Mecánica": "mecanica",
        "Ing. Química": "quimica",
        "Ing. Metalúrgica": "metalurgica",
        "Comunicaciones":"electronica_comunicaciones",
        "Computación": "electronica_computacion",
        "Control": "electronica_control"}
        nombre_archivo = ""
        if self.texto_mencion in especialidad_to_archivo:
            nombre_archivo = especialidad_to_archivo[self.texto_mencion]
        else:
            nombre_archivo = especialidad_to_archivo[self.texto_especialidad]

        path_archivo_electivas_txt = join(RUTA_ARCHIVOS,f"electivas_{nombre_archivo}.txt")
        path_archivo_electivas_json = join(RUTA_DATOS, f"electivas_{nombre_archivo}.json")

        Materia.electivas = []
        if exists(path_archivo_electivas_json):
            Logger.info("Cargando archivo de electivas desde archivo json")
            lista_electivas = []
            with open(path_archivo_electivas_json,"r", encoding = "utf-8") as archivo_materias:
                lista_materias = json.load(archivo_materias)
            for materia in lista_materias:
                Materia(materia["semestre"],
                        materia["codigo"],
                        materia["nombre"],
                        materia["ht"],
                        materia["ha"],
                        materia["hl"],
                        materia["uc"],
                        materia["nota"],
                        materia["aprobada"],
                        materia["disponible"],
                        materia["pre1"],
                        materia["pre2"],
                        materia["coreq"],
                        materia["inscrita"],
                        [Evaluacion(e["identificador"], e["nota"], e["ponderacion"], e["extra"]) for e in materia["evaluaciones"]],
                        materia["porcentual"],
                        materia["pre3"])
            Logger.info("Finalizó el cargado de electivas desde archivo json")
            return Materia.electivas[:]

        else:
            return []

    def back_press(self, window, key, *largs):
        if key == 27:
            if self.current == "GenerarHorario":
                self.transition = SlideTransition(direction="left")
                self.current = "Horario"
                self.transition = SlideTransition(direction="right")
            elif (
                self.current == "Descargo De Responsabilidad"
                or self.current == "Colaboradores"
                or self.current == "Licencias"
            ):
                self.current = "Acerca"
            elif self.current == "Evaluaciones":
                self.current = "Inicio" if self.inicio_active else "Índice"
            elif self.current == "Estadisticas":
                self.current = "Índice"
            elif self.current != "Inicio" and self.current != "Login":
                self.notas_active = False
                self.pensum_active = False
                self.inicio_active = True
                self.horario_active = False
                self.transition = SlideTransition(direction="right")
                self.current = "Inicio"
                self.transition = SlideTransition(direction="left")
                Clock.schedule_once(lambda dt: self.mostrar_materias_inicio(), 0.65)
                self.cargar_widget_notas()
                self.cargar_widget_pensum()
            return True
        else:
            return False

    def boton_appbar(self, texto):
        self.transition = SlideTransition(direction="left")
        if not self.has_screen(texto):
            if texto == "Acerca":
                self.add_widget(Acerca())
            else:
                self.add_widget(Configuracion())
                pantalla_configuracion = self.get_screen("Configuracion")
                pantalla_configuracion.tiempo_espera = self.texto_tiempo_espera
                pantalla_configuracion.tema = self.tema

        self.current = texto
        self.transition = SlideTransition(direction="right")
        self.menu_appbar.dismiss()

    @auto_save_usuario
    def actualizar_colores(self):
        self.tema = "Claro" if self.tema_ingles == "Light" else "Oscuro"

        if self.tema_ingles == "Dark":
            self.color_fondo = [0, 0, 0, 1]
            self.color_fondo_claro = [
                0.07450980392156863,
                0.07450980392156863,
                0.09411764705882353,
                1.0,
            ]
            set_status_bar_color("#131318")
            set_status_bar_icons_dark(False)
            set_navigation_bar_black(True)
            self.color_fondo_mas_claro = [
                0.12156862745098039,
                0.12156862745098039,
                0.1450980392156863,
                1.0,
            ]
            self.borde_letra_grueso = 1
            self.borde_letra_fino = 1
            self.LETRA_FUERTE = "#B2B2B2"
            self.LETRA_INTERMEDIA = "#B2B2B2"
        else:
            self.color_fondo = [1, 1, 1, 1]
            self.color_fondo_claro = [1, 1, 1, 1]
            set_status_bar_color("#FFFFFF")
            set_status_bar_icons_dark(True)
            set_navigation_bar_black(False)
            self.color_fondo_mas_claro = [0.95, 0.95, 0.95, 1]
            self.borde_letra_grueso = 0
            self.borde_letra_fino = 0
            self.LETRA_FUERTE = "#333333"
            self.LETRA_INTERMEDIA = "#404040"

        if self.has_screen("Estadisticas"):
            pantalla = self.get_screen("Estadisticas")
            pantalla.tema = self.tema
        if self.has_screen("Configuracion"):
            pantalla = self.get_screen("Configuracion")
            pantalla.tema = self.tema
        if self.has_screen("Evaluaciones"):
            pantalla = self.get_screen("Evaluaciones")
            pantalla.tema = self.tema
            if (
                not pantalla.ids.chip_porcentual.active
                and not pantalla.ids.chip_nota_extra.active
                and not pantalla.ids.chip_minima.active
                and not pantalla.ids.chip_sustitutiva.active
            ):
                pantalla.color_chip = (
                    [0.10588235294117647, 0.10588235294117647, 0.12941176470588237, 1.0]
                    if self.tema == "Oscuro"
                    else [
                        0.9607843137254902,
                        0.9490196078431372,
                        0.9803921568627451,
                        1.0,
                    ]
                )
            else:
                porcentual = pantalla.ids.chip_porcentual.active
                extra = pantalla.ids.chip_nota_extra.active
                minima = pantalla.ids.chip_minima.active
                sustitutiva = pantalla.ids.chip_sustitutiva.active

                if pantalla.ids.chip_porcentual.active:
                    pantalla.ids.chip_porcentual.active = False
                if pantalla.ids.chip_nota_extra.active:
                    pantalla.ids.chip_nota_extra.active = False
                if pantalla.ids.chip_minima.active:
                    pantalla.ids.chip_minima.active = False
                if pantalla.ids.chip_sustitutiva.active:
                    pantalla.ids.chip_sustitutiva.active = False

                pantalla.color_chip = (
                    [0.10588235294117647, 0.10588235294117647, 0.12941176470588237, 1.0]
                    if self.tema == "Oscuro"
                    else [
                        0.9607843137254902,
                        0.9490196078431372,
                        0.9803921568627451,
                        1.0,
                    ]
                )

                pantalla.ids.chip_porcentual.active = porcentual
                pantalla.ids.chip_nota_extra.active = extra
                pantalla.ids.chip_minima.active = minima
                pantalla.ids.chip_sustitutiva.active = sustitutiva

        if not self.cargar_indice:
            for widget in self.ids["menu_notas_materias"].children:
                if widget.id != "":
                    widget.md_bg_color = self.color_fondo_claro
                else:
                    widget.md_bg_color = self.color_fondo_mas_claro
        else:
            for widget in self.widgets_lista_notas:
                if widget.id != "":
                    widget.md_bg_color = self.color_fondo_claro
                else:
                    widget.md_bg_color = self.color_fondo_mas_claro

        if not self.cargar_pensum:
            for widget in self.ids["menu_pensum_materias"].children:
                if widget.id == "":
                    widget.md_bg_color = self.color_fondo_mas_claro
                else:
                    if (
                        widget.md_bg_color != self.VERDE
                        and widget.md_bg_color != self.AMARILLO
                    ):
                        widget.md_bg_color = self.color_fondo_claro
                for hijo in widget.children:
                    if hijo.id == "":
                        if self.tema == "Claro":
                            hijo.text = hijo.text.replace(
                                "[color=#B2B2B2]", "[color=#333333]"
                            ).replace("[/color]", "[/color]")
                        else:
                            hijo.text = hijo.text.replace(
                                "[color=#333333]", "[color=#B2B2B2]"
                            ).replace("[/color]", "[/color]")

                        hijo.outline_width = self.borde_letra_fino
        else:
            for widget in self.diccionario_widgets_pensum.keys():
                if widget.id == "":
                    widget.md_bg_color = self.color_fondo_mas_claro
                else:
                    if (
                        widget.md_bg_color != self.VERDE
                        and widget.md_bg_color != self.AMARILLO
                    ):
                        widget.md_bg_color = self.color_fondo_claro
                for hijo in widget.children:
                    if hijo.id == "":
                        if self.tema == "Claro":
                            hijo.text = hijo.text.replace(
                                "[color=#B2B2B2]", "[color=#333333]"
                            ).replace("[/color]", "[/color]")
                        else:
                            hijo.text = hijo.text.replace(
                                "[color=#333333]", "[color=#B2B2B2]"
                            ).replace("[/color]", "[/color]")

                        hijo.outline_width = self.borde_letra_fino


        if self.activado_bloques_horario == False:
            for box in self.pantalla_generar_horario.ids["GridLayoutHorario"].children:
                box.md_bg_color = self.color_fondo_claro

        if not self.requiere_login:
            Clock.schedule_once(
                lambda dt, inscritas=True: self.mostrar_materias_inicio(
                    inscritas=inscritas
                ),
                1.5,
            )

    def color_moradito(self):
        self.mari += 1
        if self.mari == 10:
            Clock.schedule_once(lambda dt: self.mostrar_materias_inicio(), 0.5)
            self.NARANJA_CLARO = [0.51, 0.071, 0.557, 1]
            self.NARANJA_OSCURO = [0.404, 0.031, 0.443, 1]
            self.AZUL_CLARO = [0.741, 0.082, 0.318, 1]
            self.AZUL_OSCURO = [0.596, 0.035, 0.231, 1]
            self.AZUL_MAS_CLARO = [0.808, 0.235, 0.435, 1]
            self.VERDE = [0.576, 0.106, 0.749, 1]

            if not self.cargar_pensum:
                for widget in self.ids["menu_pensum_materias"].children:
                    if widget.id != "":
                        if (
                            widget.md_bg_color != self.color_fondo_claro
                            and widget.md_bg_color != self.AMARILLO
                        ):
                            widget.md_bg_color = self.VERDE
            else:
                for widget in self.diccionario_widgets_pensum.keys():
                    if widget.id != "":
                        if (
                            widget.md_bg_color != self.color_fondo_claro
                            and widget.md_bg_color != self.AMARILLO
                        ):
                            widget.md_bg_color = self.VERDE

    def cargar_datos_usuario(self):
        ruta_json = join(RUTA_DATOS, "datos.json")
        ruta_txt = join(RUTA_ARCHIVOS, "datos.txt")
        datos_cargados = False
        if exists(ruta_json):
            with open(ruta_json, "r", encoding="utf-8") as datos:
                datos_usuario = json.load(datos)
                self.texto_nombre = datos_usuario["nombre"]
                self.texto_especialidad = datos_usuario["especialidad"]
                self.texto_mencion = datos_usuario["mencion"]
                self.tiempo_espera = datos_usuario["tiempo_espera"]
                self.guia_inicio = datos_usuario["guia_inicio"]
                self.guia_indice = datos_usuario["guia_indice"]
                self.guia_pensum = datos_usuario["guia_pensum"]
                self.guia_horario = datos_usuario["guia_horario"]
                version_guardada = datos_usuario["version"]
                self.tema_ingles = datos_usuario["tema"]
                datos_cargados = True

        elif exists(ruta_txt):
            with open(ruta_txt, "r", encoding="utf-8") as datos:
                self.texto_nombre = datos.readline().replace("\n", "")
                self.texto_especialidad = datos.readline().replace("\n", "")
                self.texto_mencion = datos.readline().replace("\n", "")
                self.tiempo_espera = float(datos.readline().replace("\n", ""))
                self.guia_inicio = eval(datos.readline().replace("\n", ""))
                self.guia_indice = eval(datos.readline().replace("\n", ""))
                self.guia_pensum = eval(datos.readline().replace("\n", ""))
                self.guia_horario = eval(datos.readline().replace("\n", ""))
                version_guardada = datos.readline().replace("\n", "")
                datos_cargados = True
            self.guardar_datos_usuario()
            os.remove(ruta_txt)

        if datos_cargados:

            migracion = False
            if version_guardada != VERSION:
                Logger.info(
                    "Cambio de versión detectado, iniciando migración de datos"
                )
                migracion = True
                migrar_datos(version_guardada)
                self.guia_inicio = True
                self.guia_horario = True
                Clock.schedule_once(self.mostrar_guia_inicio, 2.5)

            if self.tiempo_espera == 0.1:
                self.texto_tiempo_espera = "Rápida"

            Logger.info(
                "Cargando funciones get_materias, calcular_indice, unidades aprobadas y totales, actualizar colores, cargar_widget_notas y pensum."
            )
            self.get_materias(force_reload=True)
            self.calcular_indice()
            self.unidades_aprobadas_y_totales()
            self.actualizar_colores()
            self.cargar_widget_notas()
            self.cargar_widget_pensum()
            if migracion:
                Logger.info("Se detectó migración de datos, actualizando pensum")
                self.actualizar_pensum("")
                self.desactualizar_pensum("")

        else:
            Logger.info("No hay datos de usuario, redirigiendo a pantalla de login")
            self.tiempo_espera = 0.2
            self.transition = NoTransition()
            self.requiere_login = True
            self.actualizar_colores()

    # Pantalla de login
    def set_texto_especialidad(self, texto):
        verificacion = texto
        self.texto_especialidad = texto
        if verificacion == "Ing. Electrónica":
            self.texto_mencion = ""
            self.icono_especialidad = "chip"
            self.icono_mencion = "arrow-right-bold"
        elif verificacion == "Ing. Industrial":
            self.icono_especialidad = "factory"
            self.texto_mencion = "No Aplica"
            self.icono_mencion = "arrow-right-bold"
        elif verificacion == "Ing. Eléctrica":
            self.icono_especialidad = "transmission-tower"
            self.texto_mencion = "No Aplica"
            self.icono_mencion = "arrow-right-bold"
        elif verificacion == "Ing. Mecánica":
            self.icono_especialidad = "cogs"
            self.texto_mencion = "No Aplica"
            self.icono_mencion = "arrow-right-bold"
        elif verificacion == "Ing. Metalúrgica":
            self.icono_especialidad = "anvil"
            self.texto_mencion = "No Aplica"
            self.icono_mencion = "arrow-right-bold"
        elif verificacion == "Ing. Química":
            self.icono_especialidad = "test-tube"
            self.texto_mencion = "No Aplica"
            self.icono_mencion = "arrow-right-bold"

        self.menu_especialidad.dismiss()

    def set_texto_mencion(self, texto):
        self.texto_mencion = texto
        if self.texto_mencion == "Comunicaciones":
            self.icono_mencion = "signal-variant"
        elif self.texto_mencion == "Computación":
            self.icono_mencion = "laptop"
        elif self.texto_mencion == "Control":
            self.icono_mencion = "sine-wave"
        self.menu_mencion.dismiss()

    @auto_save_usuario
    def guardar_datos_login(self):
        pantalla_login = self.get_screen("Login")
        if (
            pantalla_login.ids["nombre_usuario"].text == ""
            or pantalla_login.ids["nombre_usuario"].error
        ):
            pantalla_login.ids["nombre_usuario"].error = True
        elif self.texto_especialidad == "":
            pantalla_login.ids["campo_especialidad"].error = True
        elif self.texto_mencion == "":
            pantalla_login.ids["campo_mencion"].error = True
        else:
            self.texto_nombre = pantalla_login.ids["nombre_usuario"].text
            self.current = "Inicio"
            self.guardar_datos_usuario()
            self.get_materias(force_reload=True)
            self.reiniciar_widgets()
            if self.has_screen("Horario"):
                self.cargar_datos_horario_usuario()
            self.cargar_widget_notas()
            self.cargar_widget_pensum()
            self.calcular_indice()
            self.unidades_aprobadas_y_totales()
            self.pensum_active = False
            self.inicio_active = True
            self.notas_active = False
            self.horario_active = False
            Clock.schedule_once(self.mostrar_guia_inicio, 1.2)
            Clock.schedule_once(
                lambda dt, inscritas=True: self.mostrar_materias_inicio(
                    inscritas=inscritas
                ),
                1.5,
            )
            Clock.schedule_once(
                lambda dt, cambio_tema=True: self.mostrar_materias_inicio(
                    cambio_tema=cambio_tema
                ),
                1.6,
            )
            self.remove_widget(pantalla_login)
            self.requiere_login = False

    # Cambio de pantallas
    def on_switch_tabs(self, bar: MDNavigationBar, item: MDNavigationItem, item_icon: str, item_text: str):
        self.navegacion_desactivada = True
        if item_text == "Índice":
            if self.current == "Pensum":
                self.transition = SlideTransition(direction="right")
            if self.current == "Inicio":
                self.transition = SlideTransition(direction="left")
            self.current = "Índice"
            if self.guia_indice:
                Clock.schedule_once(self.mostrar_guia_indice, 1)
            self.notas_active = True
            self.pensum_active = False
            self.inicio_active = False
            self.horario_active = False
            self.agregar_widgets_notas()

        elif item_text == "Pensum":
            if self.current == "Índice" or self.current == "Inicio":
                self.transition = SlideTransition(direction="left")
            self.current = "Pensum"
            if self.guia_pensum:
                Clock.schedule_once(self.mostrar_guia_pensum, 1)
            self.notas_active = False
            self.pensum_active = True
            self.inicio_active = False
            self.horario_active = False
            self.agregar_widgets_pensum()

        elif item_text == "Inicio":
            self.notas_active = False
            self.pensum_active = False
            self.inicio_active = True
            self.horario_active = False
            self.transition = SlideTransition(direction="right")
            if self.current != "Índice" and self.current != "Horario":
                Clock.schedule_once(lambda dt: self.mostrar_materias_inicio(), 0.5)
            self.current = "Inicio"
            self.transition = SlideTransition(direction="left")
            self.cargar_widget_notas()
            self.cargar_widget_pensum()

        elif item_text == "Horario":
            if not self.has_screen("Horario"):
                self.add_widget(Horario())
                self.pantalla_horario = self.get_screen("Horario")
                Clock.schedule_once(self.cargar_datos_horario, 0.65)
                Clock.schedule_once(self.cargar_datos_horario_usuario, 1.5)
            self.notas_active = False
            self.pensum_active = False
            self.inicio_active = False
            self.horario_active = True
            self.transition = SlideTransition(direction="left")
            self.current = "Horario"
            if self.guia_horario:
                Clock.schedule_once(self.mostrar_guia_horario, 1)
            self.transition = SlideTransition(direction="right")
            self.unidades_aprobadas_y_totales()
        Clock.schedule_once(self.activar_navegacion, 1)
        # Mostrar Anuncio instersticial
        app = MDApp.get_running_app()
        if platform == "android":
            Clock.schedule_once(
                lambda dt: app.admob.show_interstitial(), 1
            )

    def activar_navegacion(self, *args):
        self.navegacion_desactivada = False

    # Guardar Datos
    def guardar_datos(self, lista_materias_a_guardar):
        especialidad_to_archivo = {"Ing. Industrial": "industrial",
        "Ing. Eléctrica": "electrica",
        "Ing. Mecánica": "mecanica",
        "Ing. Química": "quimica",
        "Ing. Metalúrgica": "metalurgica",
        "Comunicaciones":"electronica_comunicaciones",
        "Computación": "electronica_computacion",
        "Control": "electronica_control"}

        nombre_archivo = ""
        if self.texto_mencion in especialidad_to_archivo:
            nombre_archivo = especialidad_to_archivo[self.texto_mencion]
        else:
            nombre_archivo = especialidad_to_archivo[self.texto_especialidad]

        path_archivo_materias = join(RUTA_DATOS, f"materias_{nombre_archivo}.json")

        try:
            if lista_materias_a_guardar:
                Logger.debug("Guardandos datos de materias")
                lista_diccionarios = []
                for materia in lista_materias_a_guardar:
                    lista_diccionarios.append(materia.to_dict())

                with open(path_archivo_materias, "w", encoding="utf-8") as archivo_materias:
                    json.dump(lista_diccionarios, archivo_materias, indent = 4)
                    Logger.debug("Datos de materias guardados correctamente")
            else:
                Logger.warning(
                    "El archivo de materias a guardar no es válido o está vacio, no se guardarán los datos"
                )

        except IOError as e:
            Logger.error(f"Error de disco al guardar datos: {e}")
        except Exception as e:
            Logger.error(f"Error al guardar datos de materias {e}")
                
    def guardar_datos_usuario(self):
        with open(join(RUTA_DATOS, "datos.json"), "w", encoding="utf-8") as datos:
            datos_usuario = {"nombre": self.texto_nombre,
            "especialidad": self.texto_especialidad,
            "mencion": self.texto_mencion,
            "tiempo_espera": self.tiempo_espera,
            "guia_inicio": self.guia_inicio,
            "guia_indice": self.guia_indice,
            "guia_pensum": self.guia_pensum,
            "guia_horario": self.guia_horario,
            "version": VERSION,
            "tema": self.tema_ingles}
            json.dump(datos_usuario, datos, indent = 4)

    # Pantalla inicio
    def mostrar_materias_inicio(self, inscritas=False, cambio_tema=False, *args):
        async def cargar_materias_async(
            self, es_inscritas, es_cambio_tema
        ):  # Renombrado para claridad
            grid_layout_id = (
                "grid_layout_inicio_inscritas"
                if es_inscritas
                else "grid_layout_inicio_disponibles"
            )
            grid_layout = self.ids.get(grid_layout_id)

            lista_widgets_attr = (
                "lista_materias_inicio_inscritas"
                if es_inscritas
                else "lista_materias_inicio_inscribir"
            )

            # Limpiar widgets anteriores
            for widget_existente in getattr(self, lista_widgets_attr, []):
                if widget_existente.parent:  # Solo remover si tiene padre
                    grid_layout.remove_widget(widget_existente)
            setattr(self, lista_widgets_attr, [])  # Resetear la lista de widgets

            lista_actual_widgets = []  # Lista local para los nuevos widgets

            if es_inscritas:
                lista_materias_a_mostrar = self.lista_materias_inscritas
                unidades_actuales = self.unidades_inscritas
                texto_box1_eval_str = "'+'"  # Para el botón de evaluaciones
                ripple_efectivo = True
            else:
                lista_materias_a_mostrar = self.lista_materias_para_inscribir
                unidades_actuales = self.unidades_para_inscribir
                texto_box1_eval_str = "f'{materia.codigo}'"
                ripple_efectivo = False

            for (
                materia_obj
            ) in (
                lista_materias_a_mostrar
            ):  # materia_obj para no confundir con la clase Materia
                label_text = ""
                box_layout_inicio = None
                # Box izquierda
                label_text = (
                    eval(texto_box1_eval_str, {"materia": materia_obj})
                    if texto_box1_eval_str != "'+'"
                    else "+"
                )
                box_layout_inicio = BoxConRippleInicio(
                    MDLabel(text=label_text, halign="center"),
                    ripple_effect=ripple_efectivo,
                    size_hint_y=None,
                    height=(self.height) * 0.052,
                    orientation="vertical",
                    theme_bg_color="Custom",
                    md_bg_color=self.NARANJA_CLARO,
                    radius=dp(7),
                )
                if es_inscritas:
                    box_layout_inicio.bind(
                        on_touch_down=lambda instance, touch, m=materia_obj: self.ver_evaluaciones(
                            instance, touch, m, False
                        )
                    )
                lista_actual_widgets.append(box_layout_inicio)
                # Box Central
                box_layout_inicio = BoxConRippleInicio(
                    MDLabel(
                        text=f"{materia_obj.nombre}",
                        halign="center",
                        theme_line_height="Custom",
                        line_height=0.75,
                        outline_width=self.borde_letra_fino,
                        outline_color="gray",
                    ),
                    size_hint_y=None,
                    height=(self.height) * 0.052,
                    orientation="vertical",
                    theme_bg_color="Custom",
                    md_bg_color=self.NARANJA_CLARO,
                    radius=dp(7),
                )
                box_layout_inicio.bind(
                    on_touch_down=lambda instance, touch, m=materia_obj, es_sem=False: self.doble_tap(
                        instance, touch, m, es_sem
                    )
                )
                lista_actual_widgets.append(box_layout_inicio)
                # Box derecha
                box_layout_inicio = MDBoxLayout(
                    MDLabel(text=f"{materia_obj.uc}", halign="center"),
                    size_hint_y=None,
                    height=(self.height) * 0.052,
                    orientation="vertical",
                    theme_bg_color="Custom",
                    md_bg_color=self.NARANJA_CLARO,
                    radius=dp(7),
                )
                lista_actual_widgets.append(box_layout_inicio)

            await ak.sleep(0)  # Ceder control
            # Añadir pie de tabla (Carga Total o mensaje de 'No hay materias')
            if lista_materias_a_mostrar:
                box_pie = MDBoxLayout(
                    size_hint_y=None,
                    height=(self.height) * 0.052,
                    theme_bg_color="Custom",
                    md_bg_color=self.NARANJA_OSCURO,
                    radius=dp(7),
                )
                texto_carga = (
                    "Carga Total:"
                    if unidades_actuales <= 21
                    else "Carga Total (Exceso):"
                )
                boton_info_carga = MDIconButton(
                    icon="information",
                    style="standard",
                    pos_hint={
                        "center_x": (0.26 if unidades_actuales <= 21 else 0.12),
                        "center_y": 0.5,
                    },
                    opacity=0.8,
                    theme_icon_color="Custom",
                    icon_color=("white" if self.tema == "Oscuro" else self.AZUL_CLARO),
                )
                boton_info_carga.bind(on_release=lambda x: self.aviso_carga_maxima())
                lista_actual_widgets.append(box_pie)
                box_pie = MDRelativeLayout(
                    boton_info_carga,
                    MDLabel(
                        text=texto_carga,
                        pos_hint={"center_x": 0.5, "center_y": 0.5},
                        halign="center",
                        bold=True,
                    ),
                    size_hint_y=None,
                    height=(self.height) * 0.052,
                    theme_bg_color="Custom",
                    md_bg_color=self.NARANJA_OSCURO,
                    radius=dp(7),
                )
                lista_actual_widgets.append(box_pie)
                box_pie = MDBoxLayout(
                    MDLabel(text=f"{unidades_actuales}/21", bold=True, halign="center"),
                    size_hint_y=None,
                    height=(self.height) * 0.052,
                    orientation="vertical",
                    theme_bg_color="Custom",
                    md_bg_color=self.NARANJA_OSCURO,
                    radius=dp(7),
                )
                lista_actual_widgets.append(box_pie)
            else:  # No hay materias
                mensaje_no_materias = (
                    "No hay materias inscritas"
                    if es_inscritas
                    else "Todas las materias aprobadas!"
                )
                for i in range(3):
                    box_no_materias = None
                    if i == 1:  # Columna central para el mensaje
                        box_no_materias = MDRelativeLayout(
                            MDLabel(
                                text=mensaje_no_materias,
                                pos_hint={"center_x": 0.5, "center_y": 0.5},
                                halign="center",
                                bold=True,
                            ),
                            size_hint_y=None,
                            height=(self.height) * 0.052,
                            theme_bg_color="Custom",
                            md_bg_color=self.NARANJA_CLARO,
                            radius=dp(7),
                        )
                    else:  # Columnas vacías a los lados
                        box_no_materias = MDBoxLayout(
                            size_hint_y=None,
                            height=(self.height) * 0.052,
                            theme_bg_color="Custom",
                            md_bg_color=self.NARANJA_CLARO,
                            radius=dp(7),
                        )

                    if box_no_materias:
                        lista_actual_widgets.append(box_no_materias)

            # Botón "Agregar Materias" solo para la pestaña de inscritas
            if es_inscritas:
                box_vacio = MDBoxLayout(
                    size_hint_y=None, height=dp(1)
                )  # Espaciador o placeholder
                lista_actual_widgets.append(box_vacio)

                boton_dialogo_agregar = MDButton(
                    MDButtonIcon(
                        icon="plus", theme_icon_color="Custom", icon_color="black"
                    ),
                    MDButtonText(text="[color=#000000]Materia[/color]", markup=True),
                    style="elevated",
                    pos_hint={"center_x": 0.5, "center_y": 0.5},
                    theme_bg_color="Custom",
                    md_bg_color="#4EC38F",
                )
                boton_dialogo_agregar.bind(on_release=self.dialogo_agregar_materias)
                box_boton_agregar = MDRelativeLayout(
                    boton_dialogo_agregar, size_hint_y=None, height=(self.height) * 0.1
                )
                lista_actual_widgets.append(box_boton_agregar)

            for widget in lista_actual_widgets:
                grid_layout.add_widget(widget)
            setattr(
                self, lista_widgets_attr, lista_actual_widgets
            )  # Guardar la nueva lista de widgets

        # Lógica de llamada a cargar_materias_async
        if inscritas:
            self.unidades_aprobadas_y_totales()  # Actualiza self.lista_materias_inscritas
            ak.start(
                cargar_materias_async(
                    self, es_inscritas=True, es_cambio_tema=cambio_tema
                )
            )
        else:  # Materias disponibles para inscribir
            # Solo recargar si la lista ha cambiado o si es un cambio de tema o la primera carga
            if (
                self.old_lista_materias_para_inscribir
                != self.lista_materias_para_inscribir
                or not self.lista_materias_inicio_inscribir
                or cambio_tema
            ):
                self.unidades_aprobadas_y_totales()  # Actualiza self.lista_materias_para_inscribir
                ak.start(
                    cargar_materias_async(
                        self, es_inscritas=False, es_cambio_tema=cambio_tema
                    )
                )

    def dialogo_agregar_materias(self, instance):
        lista_materias = self.get_materias()
        recycle_view_materias = RV(lista_materias)
        menu_seleccion = MDDialog(
            MDDialogIcon(
                icon="information",
                theme_icon_color="Custom",
                icon_color=self.AZUL_CLARO,
            ),
            MDDialogHeadlineText(text="Inscribir Materias"),
            MDDialogContentContainer(recycle_view_materias, orientation="vertical"),
            size_hint_x=0.9,
            radius=dp(10),
            ripple_scale=0,
            theme_focus_color="Custom",
            padding="0dp",
            hide_duration=0.5,
            state_press=0,
        )
        menu_seleccion.bind(
            on_dismiss=lambda instance, x=lista_materias: self.accion_cerrar_dialogo_agregar_materias(
                lista_materias=x
            )
        )
        boton_aceptar = MDDialogButtonContainer(
            Widget(),
            MDButton(
                MDButtonText(
                    text="[b]Aceptar[/b]",
                    theme_text_color="Custom",
                    text_color=self.CYAN,
                    markup=True,
                ),
                on_release=lambda instance, dialogo=menu_seleccion: self.cerrar_dialogo(
                    dialogo
                ),
                style="text",
            ),
        )
        menu_seleccion.add_widget(boton_aceptar)
        menu_seleccion.open()

    @auto_save_materias
    def accion_cerrar_dialogo_agregar_materias(self, lista_materias):
        self.mostrar_materias_inicio(inscritas=True)
        self.ids.scroll_inicio_inscritas.scroll_y = 1

    def mostrar_guia_inicio(self, *args):
        if self.guia_inicio:
            global VERSION
            app = MDApp.get_running_app()
            dialogo_informacion = MDDialog(
                MDDialogIcon(
                    icon="information",
                    theme_icon_color="Custom",
                    icon_color=self.AZUL_CLARO,
                ),
                MDDialogHeadlineText(text=f"[b]¡Bienvenido/a![/b]", markup=True),
                MDDialogSupportingText(
                    text=f"¡Ahora [color=#DA6304]UNEXUM[/color] es de código abierto! El código está [b][u][ref=github]disponible aquí.[/ref][/u][/b]\n\nAntes de continuar, lee la [b]Política de Privacidad[/b] y el [b]Descargo de Responsabilidad[/b] en Leer Más. Al utilizar esta aplicación aceptas estar de acuerdo con ambos.\n\n[b]Versión {VERSION}[/b]: Puedes consultar los cambios desde la playstore.",
                    theme_font_size="Custom",
                    font_size="14sp",
                    markup=True,
                    halign="left",
                    on_ref_press= (lambda instance, url = "https://github.com/SaloBarreraDev/unexum": app.abrir_enlace(url))),
                size_hint_x=0.95,
                size_hint_y=None,
                radius=[dp(10), dp(10), dp(10), dp(10)],
                ripple_duration_in_fast=0,
                ripple_duration_in_slow=0,
                theme_focus_color="Custom",
                focus_color=[1, 1, 1, 0],
                padding="0dp",
                state_press=0,
            )
            boton = MDDialogButtonContainer(
                Widget(),
                MDButton(
                    MDButtonText(
                        text="[b]Leer Más[/b]",
                        theme_text_color="Custom",
                        text_color=self.CYAN,
                        markup=True,
                    ),
                    on_release=lambda instance, dialogo=dialogo_informacion: self.leer_mas(
                        dialogo
                    ),
                    style="text",
                ),
                MDButton(
                    MDButtonText(
                        text="[b]Ok[/b]",
                        theme_text_color="Custom",
                        text_color=self.CYAN,
                        markup=True,
                    ),
                    on_release=lambda instance, dialogo=dialogo_informacion: self.cerrar_dialogo(
                        dialogo
                    ),
                    style="text",
                ),
            )
            dialogo_informacion.add_widget(boton)
            dialogo_informacion.open()
            self.guia_inicio = False

    def leer_mas(self, dialogo):
        dialogo.dismiss()
        if not self.has_screen("Acerca"):
            self.add_widget(Acerca())
        self.current = "Acerca"

    def aviso_carga_maxima(self):
        MDSnackbar(
            MDSnackbarSupportingText(
                text="La carga máxima normal es 21 U.C, pero puede ser mayor o menor en casos especiales. [color=#092B74][b][ref=dialogo_carga]Leer más[/ref][/b][/color]",
                on_ref_press=(lambda x, y: self.dialogo_carga_maxima()),
                markup=True,
                theme_text_color="Custom",
                text_color=self.LETRA_FUERTE,
            ),
            duration=5,
            pos_hint={"center_x": 0.5},
            y=dp(5),
            size_hint_x=0.95,
            theme_bg_color="Custom",
            background_color=self.color_fondo_mas_claro,
        ).open()

    def dialogo_carga_maxima(self, *args):
        dialogo_informacion = MDDialog(
            MDDialogHeadlineText(text="Carga Máxima"),
            MDDialogIcon(
                icon="information",
                theme_icon_color="Custom",
                icon_color=self.AZUL_CLARO,
            ),
            MDDialogSupportingText(
                text="Se podrá cursar hasta 3 U.C. por encima de la carga máxima establecida, a quienes cumplen con las siguientes condiciones: \n[b]1.[/b] Tener índice académico mínimo de 6. \n[b]2.[/b] Haber aprobado la totalidad de la carga académica en el lapso anterior.\n\n[b]En caso de repitiencia:[/b]\n[b]1. Repetir por primera vez:[/b] la carga máxima será igual a la carga cursada en el lapso donde fue aplazada la asignatura a repetir, en caso de varias asignaturas con la condición se toma el límite mayor. Si el índice académico es mayor a 6, se podrán tomar 2 U.C. sobre el límite.\n[b]2. Repetir por segunda vez:[/b] la carga máxima será 10 U.C. En ningún caso será superior a los créditos cursados en el lapso donde fue aplazado por segunda vez.\n[b]3. Repetir por tercera vez:[/b] sólo se podrá cursar la asignatura a repetir.\n",
                markup=True,
                halign="left",
            ),
            size_hint_x=0.95,
            size_hint_y=None,
            radius=[dp(10), dp(10), dp(10), dp(10)],
            ripple_duration_in_fast=0,
            ripple_duration_in_slow=0,
            theme_focus_color="Custom",
            focus_color=[1, 1, 1, 0],
            padding="0dp",
            state_press=0,
            spacing=0,
        )
        boton = MDDialogButtonContainer(
            Widget(),
            MDButton(
                MDButtonText(
                    text="[b]Ok[/b]",
                    theme_text_color="Custom",
                    text_color=self.CYAN,
                    markup=True,
                ),
                on_release=lambda instance, dialogo=dialogo_informacion: self.cerrar_dialogo(
                    dialogo
                ),
                style="text",
            ),
            spacing=0,
            padding=0,
            size_hint_y=0.05,
        )
        dialogo_informacion.add_widget(boton)
        dialogo_informacion.open()

    def dialogo_ubicacion_semestre(self, *args):
        dialogo_informacion = MDDialog(
            MDDialogHeadlineText(text="Ubicación en el semestre"),
            MDDialogIcon(
                icon="information",
                theme_icon_color="Custom",
                icon_color=self.AZUL_CLARO,
            ),
            MDDialogSupportingText(
                text="U.C. Aprobadas | Semestre\n0 - 18 | I\n19 - 36 | II\n37 - 55 | III\n56 - 75 | IV\n76 - 94 | V\n95 - 113 | VI\n114 - 128 | VII\n129 - 146 | VIII\n147 - 161 | IX\n162 en adelante | X"
            ),
            size_hint_x=0.9,
            size_hint_y=None,
            radius=[dp(10), dp(10), dp(10), dp(10)],
            ripple_duration_in_fast=0,
            ripple_duration_in_slow=0,
            theme_focus_color="Custom",
            focus_color=[1, 1, 1, 0],
            padding="0dp",
            state_press=0,
        )
        boton = MDDialogButtonContainer(
            Widget(),
            MDButton(
                MDButtonText(
                    text="[b]Ok[/b]",
                    theme_text_color="Custom",
                    text_color=self.CYAN,
                    markup=True,
                ),
                on_release=lambda instance, dialogo=dialogo_informacion: self.cerrar_dialogo(
                    dialogo
                ),
                style="text",
            ),
        )
        dialogo_informacion.add_widget(boton)
        dialogo_informacion.open()

    def dialogo_mencion_honorifica(self, *args):
        dialogo_informacion = MDDialog(
            MDDialogHeadlineText(text="Mención Honorífica"),
            MDDialogIcon(
                icon="information",
                theme_icon_color="Custom",
                icon_color=self.AZUL_CLARO,
            ),
            MDDialogSupportingText(
                text="[b]SUMMA CUM LAUDE:[/b] Índice académico entre 8,45 y 9,00. Ambos inclusive.\n\n[b]CUM LAUDE:[/b] Índice académico entre 8,00 y 8,44. Ambos inclusive.",
                markup=True,
            ),
            size_hint_x=0.9,
            size_hint_y=None,
            radius=[dp(10), dp(10), dp(10), dp(10)],
            ripple_duration_in_fast=0,
            ripple_duration_in_slow=0,
            theme_focus_color="Custom",
            focus_color=[1, 1, 1, 0],
            padding="0dp",
            state_press=0,
        )
        boton = MDDialogButtonContainer(
            Widget(),
            MDButton(
                MDButtonText(
                    text="[b]Ok[/b]",
                    theme_text_color="Custom",
                    text_color=self.CYAN,
                    markup=True,
                ),
                on_release=lambda instance, dialogo=dialogo_informacion: self.cerrar_dialogo(
                    dialogo
                ),
                style="text",
            ),
        )
        dialogo_informacion.add_widget(boton)
        dialogo_informacion.open()

    # Pantalla de Indice
    def cargar_widget_notas(self, *args):
        def crear_widgets(self):
            Widget_Principal.activado = False
            self.cargar_indice = True
            lista_materias = self.get_materias()
            iteraciones = len(lista_materias)
            cargador_materias = None
            iteracion = 0
            semestres = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X"]

            async def cargar_materia(*args):
                nonlocal iteracion
                await ak.sleep(0)
                try:
                    materia = lista_materias[iteracion]
                except IndexError as e:
                    cargador_materias.cancel()
                    return True

                if materia.semestre == semestres[0]:
                    semestres.remove(materia.semestre)
                    widget_semestre = MDBoxLayout(
                        MDLabel(
                            text=f"SEMESTRE {materia.semestre}",
                            bold=True,
                            halign="center",
                        ),
                        theme_bg_color="Custom",
                        md_bg_color=self.color_fondo_mas_claro,
                        size_hint_x=1,
                        size_hint_y=None,
                        height=dp(45),
                    )
                    self.widgets_lista_notas.append(widget_semestre)

                campo_texto = CampoTextoListaIndice(
                    id=f"{materia.codigo}WCT",
                    text=str(materia.nota).replace("''", ""),
                    max_height="35dp",
                )
                objeto_lista = BoxConRippleIndice(
                    LabelListaIndice(
                        text=f"[b]{materia.nombre}[/b]\n[size=14sp]{materia.uc} U.C[/size]"
                    ),
                    campo_texto,
                    id=f"{materia.codigo}WN",
                )
                objeto_lista.bind(
                    on_touch_down=lambda instance, touch, m=materia: self.ver_evaluaciones(
                        instance, touch, m, True
                    )
                )
                campo_texto.bind(
                    focus=lambda instance, value, codigo=materia.codigo: self.on_focus(
                        instance, value, codigo
                    )
                )
                self.lista_campos.append(campo_texto)
                self.widgets_lista_notas.append(objeto_lista)
                iteracion += 1

                if iteracion >= iteraciones:
                    cargador_materias.cancel()

            def iniciar_carga(*args):
                ak.start(cargar_materia())

            cargador_materias = Clock.schedule_interval(iniciar_carga, 0.1)

        if Widget_Principal.activado:
            crear_widgets(self)

    def agregar_widgets_notas(self, *args):
        async def proceso(self):
            self.cargar_indice = False
            cargador_materias = None
            numero_widget = 0
            iteraciones = self.materias_totales + 10
            await ak.sleep(0)

            async def cargar_materia(*args):
                nonlocal numero_widget
                await ak.sleep(0)
                self.ids["menu_notas_materias"].add_widget(
                    self.widgets_lista_notas[numero_widget]
                )
                numero_widget += 1
                if numero_widget == iteraciones:
                    cargador_materias.cancel()

            def iniciar_carga(*args):
                ak.start(cargar_materia(*args))

            cargador_materias = Clock.schedule_interval(
                iniciar_carga, self.tiempo_espera
            )

        if Widget_Principal.activado == False and self.cargar_indice:
            ak.start(proceso(self))

    def es_numero(self, cadena):
        try:
            float(cadena)
            return True
        except ValueError:
            return False

    def calcular_indice(self, *args):
        lista_materias = self.get_materias()
        acumulador = 0
        denominador = 0
        for materia in lista_materias:
            if self.es_numero(materia.nota):
                if materia.codigo != "EB6411":
                    acumulador += materia.nota * materia.uc
                    denominador += materia.uc
        try:
            self.indice_academico = round(acumulador / denominador, 2)
            if self.indice_academico < 8:
                self.mencion_honorifica = "-"
            elif self.indice_academico >= 8 and self.indice_academico <= 8.44:
                self.mencion_honorifica = "CUM LAUDE"
            elif self.indice_academico >= 8.45 and self.indice_academico <= 9:
                self.mencion_honorifica = "SUMMA CUM LAUDE"
        except ZeroDivisionError:
            self.indice_academico = "¡Sin notas!"
            self.mencion_honorifica = "-"

    @auto_save_materias
    def on_focus(self, instance, value, codigo):
        lista_materias = self.get_materias()
        materia = self.buscar_por_codigo(codigo)
        if not value:
            if instance.text == "":
                materia.nota = ""
                self.calcular_indice()
            else:
                if self.es_numero(instance.text):
                    if float(instance.text) >= 1 and float(instance.text) <= 9:
                        nota_redondeada = round(float(instance.text), 1)
                        materia.nota = nota_redondeada
                        instance.text = str(nota_redondeada)
                        instance.cursor = (0, 0)
                        self.calcular_indice()
                    elif float(instance.text) > 9 and float(instance.text) <= 100:
                        nota_interpolada = interpolar_nota(round(float(instance.text)))
                        materia.nota = nota_interpolada
                        instance.text = str(nota_interpolada)
                        instance.cursor = (0, 0)
                        self.calcular_indice()
                    else:
                        instance.error = True
                else:
                    instance.error = True

    def siguiente_campo_notas(self, instance):
        posicion_actual = self.lista_campos.index(instance)
        siguiente_posicion = (posicion_actual + 1) % len(self.lista_campos)
        self.lista_campos[siguiente_posicion].focus = True
        if posicion_actual + 5 > len(self.lista_campos):
            self.ids["scroll_notas"].scroll_to(self.lista_campos[siguiente_posicion])
        else:
            self.ids["scroll_notas"].scroll_to(self.lista_campos[posicion_actual + 4])

    def mostrar_guia_indice(self, *args):
        if self.guia_indice:
            dialogo_informacion = MDDialog(
                MDDialogIcon(
                    icon="information",
                    theme_icon_color="Custom",
                    icon_color=self.AZUL_CLARO,
                ),
                MDDialogHeadlineText(text="[b]Guía de [i]Índice[/i][/b]", markup=True),
                MDDialogSupportingText(
                    text="Las notas se deben ingresar en formato del reglamento [b][1.0-9.0][/b], o en la escala [b](9-100][/b].\n\n*Al ingresar las notas en la escala 9-100 éstas se convierten al formato del reglamento.\n\n *Toca dos veces en una materia para acceder a evaluaciones",
                    markup=True,
                    halign="left",
                ),
                size_hint_x=0.9,
                size_hint_y=None,
                radius=[dp(10), dp(10), dp(10), dp(10)],
                ripple_duration_in_fast=0,
                ripple_duration_in_slow=0,
                theme_focus_color="Custom",
                focus_color=[1, 1, 1, 0],
                padding="0dp",
                state_press=0,
            )
            boton = MDDialogButtonContainer(
                Widget(),
                MDButton(
                    MDButtonText(
                        text="[b]Ok[/b]",
                        theme_text_color="Custom",
                        text_color=self.CYAN,
                        markup=True,
                    ),
                    on_release=lambda instance, dialogo=dialogo_informacion: self.cerrar_dialogo(
                        dialogo
                    ),
                    style="text",
                ),
            )
            dialogo_informacion.add_widget(boton)
            dialogo_informacion.open()
            self.guia_indice = False

    def advertencia_borrar_notas(self):
        dialogo_advertencia = MDDialog(
            MDDialogIcon(
                icon="alert", theme_icon_color="Custom", icon_color=self.AMARILLO
            ),
            MDDialogHeadlineText(text="¿Confirmar?"),
            MDDialogSupportingText(
                text="Al presionar borrar las notas ingresadas en el Índice para esta especialidad y mención serán borradas.",
                halign="left",
            ),
            size_hint_x=0.9,
            size_hint_y=None,
            radius=[dp(10), dp(10), dp(10), dp(10)],
            ripple_duration_in_fast=0,
            ripple_duration_in_slow=0,
            theme_focus_color="Custom",
            focus_color=[1, 1, 1, 0],
            padding="0dp",
            state_press=0,
        )
        botones = MDDialogButtonContainer(
            Widget(),
            MDButton(
                MDButtonText(
                    text="[b]Cancelar[/b]",
                    theme_text_color="Custom",
                    text_color=self.CYAN,
                    markup=True,
                ),
                on_release=lambda instance, dialogo=dialogo_advertencia: self.cerrar_dialogo(
                    dialogo
                ),
                style="text",
            ),
            MDButton(
                MDButtonText(
                    text="Borrar", theme_text_color="Custom", text_color=self.CYAN
                ),
                on_release=lambda instance, dialogo=dialogo_advertencia: self.borrar_notas(
                    dialogo
                ),
                style="text",
            ),
            spacing="8dp",
        )
        dialogo_advertencia.add_widget(botones)
        dialogo_advertencia.open()

    @auto_save_materias
    def borrar_notas(self, dialogo):
        dialogo.dismiss()
        lista_materias = self.get_materias()
        for materia in lista_materias:
            materia.nota = "''"
        for campo in self.lista_campos:
            campo.text = ""
        self.calcular_indice()

    def ver_evaluaciones(self, instance, touch, materia, from_indice):
        def ir_a_pantalla(self, materia):
            self.notas_evaluaciones(materia)
            self.current = "Evaluaciones"
            self.transition = SlideTransition(direction="right")

        if from_indice:
            if touch.is_double_tap:
                pass
            else:
                return None

        if instance.collide_point(*touch.pos):
            instance.call_ripple_animation_methods(touch)

            if not self.has_screen("Evaluaciones"):
                self.add_widget(Evaluaciones())
                pantalla_evaluaciones = self.get_screen("Evaluaciones")
                pantalla_evaluaciones.color_chip = (
                    [0.10588235294117647, 0.10588235294117647, 0.12941176470588237, 1.0]
                    if self.tema == "Oscuro"
                    else [
                        0.9607843137254902,
                        0.9490196078431372,
                        0.9803921568627451,
                        1.0,
                    ]
                )

            pantalla_evaluaciones = self.get_screen("Evaluaciones")
            pantalla_evaluaciones.tema = self.tema
            pantalla_evaluaciones.materia = materia
            pantalla_evaluaciones.nombre_materia = materia.nombre
            extra = False
            pantalla_evaluaciones.ids.chip_porcentual.active = materia.porcentual
            pantalla_evaluaciones.ids.chip_minima.active = False
            pantalla_evaluaciones.ids.chip_sustitutiva.active = False
            grid_layout = pantalla_evaluaciones.ids.GridLayoutEvaluaciones

            # Remover widgets anteriores excepto los títulos:
            lista_para_remover = []
            for widget in grid_layout.children:
                if widget.md_bg_color != self.NARANJA_OSCURO:
                    lista_para_remover.append(widget)

            for widget in lista_para_remover:
                grid_layout.remove_widget(widget)
            lista_para_remover.clear()

            if materia.evaluaciones == []:
                for i in range(4):
                    materia.evaluaciones.append(
                        Evaluacion(f"Parcial {i+1}", "-", 25, False)
                    )

            j = 0
            columnas = ["Nombre", "Nota", "Ponderacion", "Borrar"]
            for evaluacion in materia.evaluaciones:
                if evaluacion.extra:
                    extra = True

                i = 0
                for texto in [
                    str(evaluacion.identificador),
                    (str(evaluacion.nota)),
                    str(evaluacion.ponderacion),
                    "x",
                ]:
                    if self.es_numero(texto):
                        if float(texto).is_integer():
                            texto = str(round(float(texto)))

                    if columnas[i] == "Nota" and materia.porcentual:
                        texto += "%"
                    label = MDLabel(
                        text=texto,
                        halign="center",
                        markup=True,
                        theme_line_height="Custom",
                        line_height=0.8,
                    )
                    BoxLayout = MDBoxLayout(
                        label,
                        id=f"{columnas[i]}{j}",
                        size_hint=[1, None],
                        height=dp(45),
                        orientation="vertical",
                    )
                    grid_layout.add_widget(BoxLayout)
                    if texto != "x":
                        if (evaluacion.extra and not columnas[i] == "Nombre") or (
                            not evaluacion.extra
                        ):
                            BoxLayout.bind(
                                on_touch_down=lambda instance, touch, evaluacion=evaluacion, materia=materia: self.editar_label_evaluaciones(
                                    instance, touch, evaluacion, materia
                                )
                            )

                    else:
                        BoxLayout.bind(
                            on_touch_down=lambda instance, touch, evaluacion=evaluacion, materia=materia: self.advertencia_borrar_evaluacion(
                                instance, touch, evaluacion, materia
                            )
                        )
                    i += 1
                j += 1

            pantalla_evaluaciones.ids.chip_nota_extra.active = extra
            # Boton agregar evaluaciones
            boton_dialogo_agregar = MDButton(
                MDButtonIcon(
                    icon="plus", theme_icon_color="Custom", icon_color="black"
                ),
                MDButtonText(text="[color=#000000]Evaluación[/color]", markup=True),
                style="elevated",
                pos_hint={"x": 0.85, "center_y": 0.5},
                theme_bg_color="Custom",
                md_bg_color="#4EC38F",
            )
            boton_dialogo_agregar.bind(
                on_release=lambda instance, materia=materia: self.agregar_evaluacion(
                    materia
                )
            )
            box_boton_agregar = MDRelativeLayout(
                boton_dialogo_agregar, size_hint_y=None, height=(self.height) * 0.1
            )
            grid_layout.add_widget(box_boton_agregar)

            # ir a la pantalla
            Clock.schedule_once(
                lambda dt, self=self, materia=materia: ir_a_pantalla(self, materia), 0.5
            )
            return True

    def notas_evaluaciones(self, materia):
        pantalla = self.get_screen("Evaluaciones")
        lista_materias = self.get_materias()
        lista_evaluaciones = copy.deepcopy(materia.evaluaciones)
        nota_final = 0
        numero_evaluaciones = 0
        nota_total = 0
        ponderacion_total = 0
        puntos_extra = 0
        numerador_media_porcentual = 0
        indice = self.indice_academico

        if not self.es_numero(indice):
            indice = 0

        if materia.porcentual:
            for evaluacion in lista_evaluaciones:
                if self.es_numero(evaluacion.nota):
                    evaluacion.nota = round(
                        (evaluacion.nota * evaluacion.ponderacion) / 100, 2
                    )

        for evaluacion in lista_evaluaciones:
            if not evaluacion.extra:
                ponderacion_total += evaluacion.ponderacion
            if self.es_numero(evaluacion.nota):
                if not evaluacion.extra:
                    numero_evaluaciones += 1
                    nota_total += evaluacion.nota
                    numerador_media_porcentual += (
                        evaluacion.nota / evaluacion.ponderacion
                    )
                else:
                    puntos_extra = evaluacion.nota

        if numero_evaluaciones:
            pantalla.media_porcentual = round(
                numerador_media_porcentual / numero_evaluaciones * 100
            )
            pantalla.media = round(nota_total / numero_evaluaciones, 2)
        else:
            pantalla.media_porcentual = 0
            pantalla.media = 0

        pantalla.nota_total = nota_total
        if ponderacion_total:
            nota_final = round(nota_total / ponderacion_total * 100, 2)
        nota_final += puntos_extra
        pantalla.nota_final = nota_final
        pantalla.nota_pasar = (
            round((50 - nota_final) * (ponderacion_total / 100), 2)
            if ((50 - nota_final) * (ponderacion_total / 100)) > 0
            else "-"
        )
        pantalla.nota_sustituir = (
            round((37.5 - nota_final) * ((ponderacion_total / 100)), 2)
            if ((37.5 - nota_final) * ((ponderacion_total / 100))) > 0
            else "-"
        )
        pantalla.ponderacion_total = ponderacion_total

        uc_aprobadas = 0
        for materias in lista_materias:
            if self.es_numero(materias.nota):
                if materias.codigo != "EB6411":
                    uc_aprobadas += materias.uc
        try:
            pantalla.aporte = round(
                (
                    (
                        indice * uc_aprobadas
                        + interpolar_nota(round(nota_final)) * materia.uc
                    )
                    / (uc_aprobadas + materia.uc)
                )
                - indice,
                3,
            )
        except ZeroDivisionError:
            pantalla.aporte = 0

    def editar_label_evaluaciones(self, box_layout, touch, evaluacion, materia):
        pantalla_evaluaciones = self.get_screen("Evaluaciones")
        if pantalla_evaluaciones.ids.chip_minima.active:
            pantalla_evaluaciones.ids.chip_minima.active = False
        if pantalla_evaluaciones.ids.chip_sustitutiva.active:
            pantalla_evaluaciones.ids.chip_sustitutiva.active = False

        def editar(self, campo, focus, box_layout, evaluacion, materia):
            if not focus:
                if "Nombre" in box_layout.id:
                    evaluacion.identificador = campo.text
                    box_layout.children[0].text = campo.text
                elif "Nota" in box_layout.id:
                    if self.es_numero(campo.text):
                        nota = float(campo.text)
                        if materia.porcentual:
                            if nota > 100 or nota < 0:
                                campo.error = True
                            else:
                                campo.error = False
                        else:
                            if nota > evaluacion.ponderacion or nota < 0:
                                campo.error = True
                            else:
                                campo.error = False
                    else:
                        campo.error = True

                    if not campo.error:
                        evaluacion.nota = round(float(campo.text), 2)
                        box_layout.children[0].text = (
                            f"{campo.text}%" if materia.porcentual else campo.text
                        )
                        self.notas_evaluaciones(materia)
                    else:
                        evaluacion.nota = "-"
                        box_layout.children[0].text = (
                            "-%" if materia.porcentual else "-"
                        )
                        self.notas_evaluaciones(materia)

                elif "Ponderacion" in box_layout.id:
                    if self.es_numero(campo.text):
                        ponderacion = float(campo.text)
                        nota = evaluacion.nota if evaluacion.nota != "-" else 0
                        if materia.porcentual:
                            if ponderacion <= 0:
                                campo.error = True
                            else:
                                campo.error = False
                        else:
                            if ponderacion < nota or ponderacion <= 0:
                                campo.error = True
                            else:
                                campo.error = False
                    else:
                        campo.error = True

                    if not campo.error:
                        evaluacion.ponderacion = round(float(campo.text), 2)
                        box_layout.children[0].text = campo.text
                        self.notas_evaluaciones(materia)

                self.guardar_datos(self.get_materias())

        if box_layout.collide_point(*touch.pos):
            texto_defecto = ""
            titulo = "Editar"
            tipo_campo = ""
            if "Nombre" in box_layout.id:
                texto_defecto = str(evaluacion.identificador)
                titulo += " nombre"
                tipo_campo = "text"
            elif "Nota" in box_layout.id:
                texto_defecto = str(evaluacion.nota)
                titulo += " nota"
                tipo_campo = "number"
            elif "Ponderacion" in box_layout.id:
                texto_defecto = str(evaluacion.ponderacion)
                titulo += " ponderación"
                tipo_campo = "number"

            campo_texto = MDTextField(
                text=texto_defecto,
                pos_hint={"center_x": 0.5},
                max_height=dp(40),
                write_tab=False,
                multiline=False,
                use_bubble=False,
                halign="center",
                input_type=tipo_campo,
            )
            dialogo_advertencia = MDDialog(
                MDDialogSupportingText(
                    text=titulo, theme_font_size="Custom", font_size="20sp"
                ),
                MDDialogContentContainer(campo_texto, orientation="vertical"),
                radius=[dp(15), dp(15), dp(15), dp(15)],
                ripple_duration_in_fast=0,
                ripple_duration_in_slow=0,
                theme_focus_color="Custom",
                focus_color=[1, 1, 1, 0],
                padding="0dp",
                state_press=0,
            )
            botones = MDDialogButtonContainer(
                Widget(),
                MDButton(
                    MDButtonText(
                        text="[b]Aceptar[/b]",
                        theme_text_color="Custom",
                        text_color=self.CYAN,
                        markup=True,
                    ),
                    on_release=lambda instance, dialogo=dialogo_advertencia: self.cerrar_dialogo(
                        dialogo
                    ),
                    style="text",
                ),
            )

            dialogo_advertencia.add_widget(botones)
            dialogo_advertencia.open()
            campo_texto.bind(
                focus=lambda instance, focus, box_layout=box_layout, evaluacion=evaluacion, materia=materia: editar(self,
                    instance, focus, box_layout, evaluacion, materia
                )
            )

            return True

    def advertencia_borrar_evaluacion(
        self, boxlayout, touch, evaluacion, materia, extra=False
    ):
        if extra or boxlayout.collide_point(*touch.pos):
            dialogo_advertencia = MDDialog(
                MDDialogIcon(
                    icon="alert", theme_icon_color="Custom", icon_color=self.AMARILLO
                ),
                MDDialogHeadlineText(text="¿Confirmar?"),
                size_hint_x=0.9,
                size_hint_y=None,
                radius=[dp(10), dp(10), dp(10), dp(10)],
                ripple_duration_in_fast=0,
                ripple_duration_in_slow=0,
                theme_focus_color="Custom",
                focus_color=[1, 1, 1, 0],
                padding="0dp",
                state_press=0,
            )
            botones = MDDialogButtonContainer(
                Widget(),
                MDButton(
                    MDButtonText(
                        text="[b]Cancelar[/b]",
                        theme_text_color="Custom",
                        text_color=self.CYAN,
                        markup=True,
                    ),
                    on_release=lambda instance, dialogo=dialogo_advertencia: self.cerrar_dialogo(
                        dialogo
                    ),
                    style="text",
                ),
                MDButton(
                    MDButtonText(
                        text="Borrar", theme_text_color="Custom", text_color=self.CYAN
                    ),
                    on_release=lambda instance, dialogo=dialogo_advertencia, box=boxlayout, e=evaluacion, m=materia, ex=extra: self.borrar_evaluacion(
                        dialogo, box, e, m, ex
                    ),
                    style="text",
                ),
                spacing="8dp",
            )
            dialogo_advertencia.add_widget(botones)
            dialogo_advertencia.open()
            return True

    @auto_save_materias
    def borrar_evaluacion(self, dialogo, boxlayout, evaluacion, materia, extra=False):
        dialogo.dismiss()
        materia.evaluaciones.remove(evaluacion)
        pantalla_evaluaciones = self.get_screen("Evaluaciones")
        # Desactivar chips
        if pantalla_evaluaciones.ids.chip_minima.active:
            pantalla_evaluaciones.ids.chip_minima.active = False
        if pantalla_evaluaciones.ids.chip_sustitutiva.active:
            pantalla_evaluaciones.ids.chip_sustitutiva.active = False

        grid_layout = pantalla_evaluaciones.ids["GridLayoutEvaluaciones"]
        if evaluacion.extra:
            pantalla_evaluaciones.ids.chip_nota_extra.active = False
        fila = (grid_layout.children.index(boxlayout) - 1) // 4
        box_a_borrar = []
        for box_layout in grid_layout.children:
            cada_fila = (grid_layout.children.index(box_layout) - 1) // 4
            if cada_fila == fila:
                box_a_borrar.append(box_layout)

        for box_layout in box_a_borrar:
            grid_layout.remove_widget(box_layout)

        self.notas_evaluaciones(materia)

        pantalla_evaluaciones.ids.scroll_evaluaciones.scroll_y = 1

    @auto_save_materias
    def agregar_evaluacion(self, materia):
        pantalla_evaluaciones = self.get_screen("Evaluaciones")
        gridlayout = pantalla_evaluaciones.ids.GridLayoutEvaluaciones
        # Desactivar chips
        if pantalla_evaluaciones.ids.chip_minima.active:
            pantalla_evaluaciones.ids.chip_minima.active = False
        if pantalla_evaluaciones.ids.chip_sustitutiva.active:
            pantalla_evaluaciones.ids.chip_sustitutiva.active = False
        j = len(materia.evaluaciones)
        i = 0
        columnas = ["Nombre", "Nota", "Ponderacion", "Borrar"]
        evaluacion_nueva = Evaluacion("Parcial", "-", 25, False)
        materia.evaluaciones.append(evaluacion_nueva)

        for texto in [
            str(evaluacion_nueva.identificador),
            str(evaluacion_nueva.nota),
            str(evaluacion_nueva.ponderacion),
            "x",
        ]:
            label = MDLabel(
                text=texto,
                halign="center",
                markup=True,
                theme_line_height="Custom",
                line_height=0.8,
            )
            BoxLayout = MDBoxLayout(
                label, id=f"{columnas[i]}{j}", size_hint=[1, None], height=dp(45)
            )
            gridlayout.add_widget(BoxLayout, index=1)
            if texto != "x":
                BoxLayout.bind(
                    on_touch_down=lambda instance, touch, evaluacion=evaluacion_nueva, materia=materia: self.editar_label_evaluaciones(
                        instance, touch, evaluacion, materia
                    )
                )
            else:
                BoxLayout.bind(
                    on_touch_down=lambda instance, touch, evaluacion=evaluacion_nueva, materia=materia: self.advertencia_borrar_evaluacion(
                        instance, touch, evaluacion, materia
                    )
                )
            i += 1

        self.notas_evaluaciones(materia)

    @auto_save_materias
    def cambio_porcentual(self, chip):
        pantalla_evaluaciones = self.get_screen("Evaluaciones")
        materia = pantalla_evaluaciones.materia
        grid_layout = pantalla_evaluaciones.ids.GridLayoutEvaluaciones
        # Desactivar chips
        if pantalla_evaluaciones.ids.chip_minima.active:
            pantalla_evaluaciones.ids.chip_minima.active = False
        if pantalla_evaluaciones.ids.chip_sustitutiva.active:
            pantalla_evaluaciones.ids.chip_sustitutiva.active = False
        if materia.porcentual != chip.active:
            materia.porcentual = chip.active
            if chip.active:
                for evaluacion in materia.evaluaciones:
                    if self.es_numero(evaluacion.nota):
                        evaluacion.nota = round(
                            (evaluacion.nota / evaluacion.ponderacion) * 100, 2
                        )
            else:
                for evaluacion in materia.evaluaciones:
                    if self.es_numero(evaluacion.nota):
                        evaluacion.nota = round(
                            (evaluacion.nota * evaluacion.ponderacion) / 100, 2
                        )

            # Actualizar labels
            i = 1
            for boxlayout in grid_layout.children:
                if "Nota" in boxlayout.id:
                    nota = str(materia.evaluaciones[-i].nota)
                    if self.es_numero(nota):
                        if float(nota).is_integer():
                            nota = str(round(float(nota)))

                    boxlayout.children[0].text = nota + (
                        "%" if materia.porcentual else ""
                    )
                    i += 1

            self.notas_evaluaciones(materia)

    @auto_save_materias
    def add_nota_extra(self, chip):
        pantalla_evaluaciones = self.get_screen("Evaluaciones")
        # Desactivar chips
        if pantalla_evaluaciones.ids.chip_minima.active:
            pantalla_evaluaciones.ids.chip_minima.active = False
        if pantalla_evaluaciones.ids.chip_sustitutiva.active:
            pantalla_evaluaciones.ids.chip_sustitutiva.active = False
        materia = pantalla_evaluaciones.materia
        gridlayout = pantalla_evaluaciones.ids.GridLayoutEvaluaciones
        ya_agregada = False
        evaluacion_borrar = None
        j = len(materia.evaluaciones)
        i = 0

        for evaluacion in materia.evaluaciones:
            if evaluacion.extra:
                ya_agregada = True
                evaluacion_borrar = evaluacion

        if chip.active and not ya_agregada:
            columnas = ["Nombre", "Nota", "Ponderacion", "Borrar"]
            evaluacion_nueva = Evaluacion("Nota extra", "-", 5, True)
            materia.evaluaciones.append(evaluacion_nueva)

            for texto in [
                str(evaluacion_nueva.identificador),
                str(evaluacion_nueva.nota),
                str(evaluacion_nueva.ponderacion),
                "x",
            ]:
                label = MDLabel(text=texto, halign="center")
                BoxLayout = MDBoxLayout(
                    label, id=f"{columnas[i]}{j}", size_hint=[1, None], height=dp(40)
                )
                gridlayout.add_widget(BoxLayout, index=1)
                if columnas[i] == "Nota" or columnas[i] == "Ponderacion":
                    BoxLayout.bind(
                        on_touch_down=lambda instance, touch, evaluacion=evaluacion_nueva, materia=materia: self.editar_label_evaluaciones(
                            instance, touch, evaluacion, materia
                        )
                    )
                elif columnas[i] == "Borrar":
                    BoxLayout.bind(
                        on_touch_down=lambda instance, touch, evaluacion=evaluacion_nueva, materia=materia: self.advertencia_borrar_evaluacion(
                            instance, touch, evaluacion, materia
                        )
                    )
                i += 1

            self.notas_evaluaciones(materia)

        elif not chip.active and ya_agregada:
            box_a_enviar = None
            for boxlayout in gridlayout.children:
                try:
                    if boxlayout.children[0].text == "Nota extra":
                        box_a_enviar = boxlayout
                except AttributeError as e:
                    pass

            self.advertencia_borrar_evaluacion(
                box_a_enviar, [], evaluacion_borrar, materia, True
            )

    def nota_minima(self, chip, sustitutiva=False):
        pantalla_evaluaciones = self.get_screen("Evaluaciones")
        materia = pantalla_evaluaciones.materia
        nota_pasar = (
            0
            if pantalla_evaluaciones.nota_pasar == "No"
            else pantalla_evaluaciones.nota_pasar
        )
        nota_sustituir = (
            0
            if pantalla_evaluaciones.nota_sustituir == "No"
            else pantalla_evaluaciones.nota_sustituir
        )
        gridlayout = pantalla_evaluaciones.ids.GridLayoutEvaluaciones
        texto_en_label = "-%" if materia.porcentual else "-"

        if sustitutiva:
            pantalla_evaluaciones.ids.chip_minima.active = False
        else:
            pantalla_evaluaciones.ids.chip_sustitutiva.active = False

        if chip.active:
            sin_evaluar = 0
            for evaluacion in materia.evaluaciones:
                if evaluacion.nota == "-" and not evaluacion.extra:
                    sin_evaluar += evaluacion.ponderacion

            notas_necesarias = []
            nota_buscar = None
            if nota_pasar > sin_evaluar or sustitutiva:
                if not sustitutiva:
                    MDSnackbar(
                        MDSnackbarText(
                            text="No es posible aprobar directamente",
                            halign="left",
                            bold=True,
                        ),
                        MDSnackbarSupportingText(
                            text=f"La nota necesaria para aprobar la materia ({nota_pasar}) no se puede obtener en las evaluaciones restantes. Intenta con Nota Sustitutiva.",
                            theme_text_color="Custom",
                            text_color=self.LETRA_FUERTE,
                        ),
                        duration=8,
                        pos_hint={"center_x": 0.5},
                        y=dp(5),
                        size_hint_x=0.8,
                        theme_bg_color="Custom",
                        background_color=self.color_fondo_mas_claro,
                    ).open()
                    chip.active = False
                else:
                    if nota_sustituir > sin_evaluar:
                        MDSnackbar(
                            MDSnackbarText(
                                text="No es posible aprobar la materia",
                                halign="left",
                                bold=True,
                            ),
                            MDSnackbarSupportingText(
                                text=f"La nota necesaria para sustituir ({nota_sustituir}) no se puede obtener en las evaluaciones restantes.",
                                theme_text_color="Custom",
                                text_color=self.LETRA_FUERTE,
                            ),
                            duration=8,
                            pos_hint={"center_x": 0.5},
                            y=dp(5),
                            size_hint_x=0.8,
                            theme_bg_color="Custom",
                            background_color=self.color_fondo_mas_claro,
                        ).open()
                        chip.active = False
                    else:
                        nota_buscar = nota_sustituir
            else:
                nota_buscar = nota_pasar

            if nota_buscar:
                if materia.porcentual:
                    for evaluacion in materia.evaluaciones:
                        if evaluacion.nota == "-" and not evaluacion.extra:
                            notas_necesarias.append(
                                round(
                                    (
                                        (evaluacion.ponderacion / sin_evaluar)
                                        * nota_buscar
                                    )
                                    / evaluacion.ponderacion
                                    * 100,
                                    2,
                                )
                            )
                        elif evaluacion.nota == "-" and evaluacion.extra:
                            notas_necesarias.append("Extra")
                else:
                    for evaluacion in materia.evaluaciones:
                        if evaluacion.nota == "-" and not evaluacion.extra:
                            notas_necesarias.append(
                                round(
                                    (evaluacion.ponderacion / sin_evaluar)
                                    * nota_buscar,
                                    2,
                                )
                            )
                        elif evaluacion.nota == "-" and evaluacion.extra:
                            notas_necesarias.append("Extra")

                # Cambiar flotantes a enteros
                notas_necesarias2 = notas_necesarias[:]

                for nota in notas_necesarias:
                    if self.es_numero(nota):
                        if float(nota).is_integer():
                            notas_necesarias2.append(str(round(float(nota))))
                        else:
                            notas_necesarias2.append(nota)
                    else:
                        notas_necesarias2.append(nota)

                notas_necesarias = notas_necesarias2[:]

                for boxlayout in gridlayout.children:
                    if "Nota" in boxlayout.id:
                        label = boxlayout.children[0]
                        if (
                            label.text == texto_en_label
                            and notas_necesarias[-1] != "Extra"
                        ):
                            label.text = (
                                f"[b][i]{notas_necesarias[-1]}%[/i][/b]"
                                if materia.porcentual
                                else f"[b][i]{notas_necesarias[-1]}[/i][/b]"
                            )
                            notas_necesarias.pop(-1)
                        elif (
                            label.text == texto_en_label
                            and notas_necesarias[-1] == "Extra"
                        ):
                            notas_necesarias.pop(-1)
            else:
                if not nota_pasar or not nota_sustituir:
                    text = "sustituir" if sustitutiva else "aprobar"
                    MDSnackbar(
                        MDSnackbarSupportingText(
                            text=f"Ya se alcazó la nota necesaria para {text}.",
                            theme_text_color="Custom",
                            text_color=self.LETRA_FUERTE,
                        ),
                        duration=8,
                        pos_hint={"center_x": 0.5},
                        y=dp(5),
                        size_hint_x=0.8,
                        theme_bg_color="Custom",
                        background_color=self.color_fondo_mas_claro,
                    ).open()
                    chip.active = False

        else:
            for boxlayout in gridlayout.children:
                if "Nota" in boxlayout.id:
                    label = boxlayout.children[0]
                    if "[i]" in label.text:
                        label.text = texto_en_label

    def mostrar_guia_evaluaciones(self):
        dialogo_informacion = MDDialog(
            MDDialogIcon(
                icon="information",
                theme_icon_color="Custom",
                icon_color=self.AZUL_CLARO,
            ),
            MDDialogHeadlineText(text="Guía Evaluaciones", markup=True),
            MDDialogSupportingText(
                text="[b]Nota final[/b]: Suma de las notas de cada evaluación, llevada a 100 puntos.\n\n[b]Media y Media porcentual:[/b] Nota media obtenida en las evaluaciones.\n\n[b]Aporte al índice:[/b] Aumento o reducción del índice actual en caso de culminar la materia con la nota final mostrada.\n\n[b]Nota extra:[/b] Nota que no se incluye en la ponderación y se suma directamente.\n\n[b]Nota mínima y Nota sustitutiva:[/b] Nota mínima requerida, distribuida equitativamente, necesaria para aprobar o sustituir.",
                theme_font_size="Custom",
                font_size="14sp",
                markup=True,
                halign="left",
            ),
            size_hint_x=0.95,
            size_hint_y=None,
            radius=[dp(10), dp(10), dp(10), dp(10)],
            ripple_duration_in_fast=0,
            ripple_duration_in_slow=0,
            theme_focus_color="Custom",
            focus_color=[1, 1, 1, 0],
            padding="0dp",
            state_press=0,
        )
        boton = MDDialogButtonContainer(
            Widget(),
            MDButton(
                MDButtonText(
                    text="[b]Ok[/b]",
                    theme_text_color="Custom",
                    text_color=self.CYAN,
                    markup=True,
                ),
                on_release=lambda instance, dialogo=dialogo_informacion: self.cerrar_dialogo(
                    dialogo
                ),
                style="text",
            ),
        )
        dialogo_informacion.add_widget(boton)
        dialogo_informacion.open()

    def ir_a_estadisticas(self):
        if not self.has_screen("Estadisticas"):
            self.add_widget(Estadisticas())
            pantalla = self.get_screen("Estadisticas")
            pantalla.tema = self.tema
        self.transition = SlideTransition(direction="down")
        self.current = "Estadisticas"
        self.transition = SlideTransition(direction="up")

    def grafico(self, tipo):
        from kivy.metrics import Metrics

        pantalla_estadisticas = self.get_screen("Estadisticas")
        fig, ax = plt.subplots()
        lista_materias = self.get_materias()
        if tipo == "Materia":
            nombres = []
            notas = []
            codigos = []
            for materia in lista_materias:
                if materia.nota != "''" and materia.nota != "":
                    nombres.append(materia.nombre)
                    notas.append(materia.nota)
                    codigos.append(materia.codigo[:2])

            color_map = {
                "II": "OrangeRed",
                "IE": "green",
                "EL": "blue",
                "IM": "gray",
                "IQ": "purple",
                "MT": "orange",
                "EB": tuple(self.NARANJA_CLARO),
                "BDE": tuple(self.NARANJA_CLARO),
                "Se": tuple(self.NARANJA_CLARO),
            }
            colores_marcadores = [color_map[cod] for cod in codigos]
            datosx = nombres
            datosy = notas
            limitex = 20
            titulo = "Notas por Materia"
            labely = "Notas"
            labelx = "Materias"
            rotacion = 90

        elif tipo == "Semestre":
            semestres = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X"]
            semestres_validos = []
            indices = []
            for semestre in semestres:
                acumulador = 0
                denominador = 0
                for materia in lista_materias:
                    if materia.semestre == semestre:
                        if self.es_numero(materia.nota):
                            if materia.codigo != "EB6411":
                                acumulador += materia.nota * materia.uc
                                denominador += materia.uc
                if denominador:
                    indice = round(acumulador / denominador, 2)
                    indices.append(indice)
                    semestres_validos.append(semestre)

            datosx = semestres_validos
            datosy = indices
            limitex = 10
            titulo = "Índice por Semestre"
            labely = "Índice"
            labelx = "Semestre"
            rotacion = 0

        elif tipo == "Progresion":
            semestres = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X"]
            semestres_validos = []
            indices = []
            for semestre in semestres:
                acumulador = 0
                denominador = 0
                valido = False
                for materia in lista_materias:
                    if materia.semestre in semestres[: semestres.index(semestre) + 1]:
                        if self.es_numero(materia.nota):
                            if materia.codigo != "EB6411":
                                acumulador += materia.nota * materia.uc
                                denominador += materia.uc
                    if materia.semestre == semestre:
                        if self.es_numero(materia.nota):
                            valido = True

                if denominador and valido:
                    indice = round(acumulador / denominador, 2)
                    indices.append(indice)
                    semestres_validos.append(semestre)

            datosx = semestres_validos
            datosy = indices
            limitex = 10
            titulo = "Progresión de Índice"
            labely = "Índice"
            labelx = "Semestre"
            rotacion = 0

        factor = Metrics.density
        ax.plot(
            datosx,
            datosy,
            marker="o",
            markersize=round(3 * factor),
            color=tuple(self.NARANJA_CLARO),
            zorder=4,
            linewidth=2 * factor,
        )
        fig.set_facecolor(tuple(self.color_fondo_claro))
        ax.set_facecolor(tuple(self.color_fondo_claro))
        ax.set_ylim(1, 10)
        ax.set_xlim(-1, limitex)
        ax.set_title(titulo, {"color": self.LETRA_FUERTE, "fontsize": 16 * factor})
        ax.set_ylabel(
            labely, {"color": self.LETRA_FUERTE, "fontsize": 14 * factor}, labelpad=0.45
        )
        ax.set_xlabel(labelx, {"color": self.LETRA_FUERTE, "fontsize": 14 * factor})
        for lado in ["left", "right", "top", "bottom"]:
            ax.spines[lado].set_color(self.LETRA_FUERTE)
        ax.set_yticks(range(1, 11, 1))
        ax.set_yticks(
            [1.5, 2.5, 3.5, 4.5, 5.5, 6.5, 7.5, 8.5, 9.5],
            ["1.5", "2.5", "3.5", "4.5", "5.5", "6.5", "7.5", "8.5", "9.5"],
            minor=True,
        )
        ax.tick_params(
            axis="x",
            which="major",
            labelrotation=rotacion,
            labelsize=7 * factor,
            labelcolor=self.LETRA_FUERTE,
            color=self.LETRA_FUERTE,
        )
        ax.tick_params(
            axis="y",
            which="major",
            labelsize=7 * factor,
            pad=2,
            grid_linestyle="-",
            labelcolor=self.LETRA_FUERTE,
            color=self.LETRA_FUERTE,
        )
        ax.tick_params(
            axis="y",
            which="minor",
            labelsize=5.5 * factor,
            pad=2,
            grid_linestyle="-",
            labelcolor=self.LETRA_FUERTE,
            color=self.LETRA_FUERTE,
        )
        ax.grid(True, which="major", axis="y", alpha=0.5, color="gray", zorder=0)
        ax.grid(True, which="minor", axis="y", alpha=0.25, color="gray", zorder=1)
        ax.grid(True, which="major", axis="x", alpha=0.5, color="gray", zorder=2)
        plt.subplots_adjust(bottom=0.4)
        if tipo != "Materia":
            for i, valor_y in enumerate(datosy):
                ax.text(
                    i,
                    valor_y + 0.3,
                    str(valor_y),
                    {"color": self.LETRA_FUERTE},
                    ha="center",
                    va="bottom",
                    fontsize=6 * factor,
                )
        else:
            ax.axhline(
                float(
                    (
                        self.indice_academico
                        if self.indice_academico != "¡Sin notas!"
                        else 0
                    )
                ),
                color=tuple(self.AZUL_MAS_CLARO),
                linestyle="--",
                zorder=3,
                linewidth=2 * factor,
            )
            ax.scatter(
                datosx, datosy, c=colores_marcadores, s=round(25 * factor), zorder=5
            )

        pantalla_estadisticas.figure_wgt.figure = fig

    def mostrar_guia_grafico(self, *args):
        dialogo_informacion = MDDialog(
            MDDialogIcon(
                icon="information",
                theme_icon_color="Custom",
                icon_color=self.AZUL_CLARO,
            ),
            MDDialogHeadlineText(text="[b]Guía de [i]Gráficos[/i][/b]", markup=True),
            MDDialogSupportingText(
                text="[b]Gráfico por materias:[/b] Los colores de los marcadores representan las distintas especialidades de cada materia. La línea segmentada representa el índice.\n\n[b]Gráfico por semestre:[/b] Representa el índice individual de cada semestre.\n\n[b]Gráfico de progresión:[/b] Representa el índice acumulado hasta cada semestre.",
                markup=True,
                halign="left",
            ),
            size_hint_x=0.9,
            size_hint_y=None,
            radius=[dp(10), dp(10), dp(10), dp(10)],
            ripple_duration_in_fast=0,
            ripple_duration_in_slow=0,
            theme_focus_color="Custom",
            focus_color=[1, 1, 1, 0],
            padding="0dp",
            state_press=0,
        )
        boton = MDDialogButtonContainer(
            Widget(),
            MDButton(
                MDButtonText(
                    text="[b]Ok[/b]",
                    theme_text_color="Custom",
                    text_color=self.CYAN,
                    markup=True,
                ),
                on_release=lambda instance, dialogo=dialogo_informacion: self.cerrar_dialogo(
                    dialogo
                ),
                style="text",
            ),
        )
        dialogo_informacion.add_widget(boton)
        dialogo_informacion.open()

    # Pantalla de Pensum
    def cargar_widget_pensum(self, *args):
        def cargar_widgets(self):
            self.ids["indicador_progreso_carga"].active = True
            Widget_Principal.activado_pensum = False
            lista_materias = self.get_materias()
            iteraciones = len(lista_materias)
            cargador_materias = None
            iteracion = 0
            semestres = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X"]

            async def cargar_materia(*args):
                nonlocal iteracion
                await ak.sleep(0)
                try:
                    materia = lista_materias[iteracion]
                except IndexError as e:
                    cargador_materias.cancel()
                    return True

                iteracion += 1
                if materia.semestre == semestres[0]:
                    semestres.remove(materia.semestre)
                    widget_semestre = MDBoxLayout(
                        MDLabel(
                            text=f"SEMESTRE {materia.semestre}",
                            bold=True,
                            halign="center",
                        ),
                        theme_bg_color="Custom",
                        md_bg_color=self.color_fondo_mas_claro,
                        size_hint_x=1,
                        size_hint_y=None,
                        height=dp(45),
                    )
                    widget_semestre.bind(
                        on_touch_down=lambda instance, touch, materia=materia, es_semestre=True, semestre=materia.semestre: self.doble_tap(
                            instance, touch, materia, es_semestre, semestre
                        )
                    )
                    self.diccionario_widgets_pensum[widget_semestre] = materia.semestre

                check_box = CheckBoxPensum(id=materia.codigo)
                objeto_lista = BoxConRipplePensum(
                    LabelListaPensum(
                        text=f"[b]{materia.nombre}\n[size=14sp][color={('#B2B2B2' if self.tema=='Oscuro' else '#333333')}]Código: {materia.codigo}[/b]\n{materia.uc} U.C[/color][/size]"
                    ),
                    check_box,
                    id=f"{materia.codigo}WP",
                    theme_bg_color="Custom",
                )

                if materia.aprobada:
                    check_box.active = True
                    objeto_lista.md_bg_color = self.VERDE
                elif materia.disponible:
                    objeto_lista.md_bg_color = self.AMARILLO
                else:
                    objeto_lista.md_bg_color = self.color_fondo_claro

                check_box.bind(
                    active=lambda checkbox, value, codigo=materia.codigo, objeto_lista=objeto_lista: self.aprobar_materia(
                        checkbox, value, codigo, objeto_lista
                    )
                )

                self.diccionario_checkboxs_pensum[check_box] = materia.codigo
                objeto_lista.bind(
                    on_touch_down=lambda instance, touch, materia=materia, es_semestre=False, semestre="": self.doble_tap(
                        instance, touch, materia, es_semestre, semestre
                    )
                )
                self.diccionario_widgets_pensum[objeto_lista] = materia.codigo

            def iniciar_carga(*args):
                nonlocal iteracion
                if iteracion >= iteraciones:
                    cargador_materias.cancel()
                    self.ids["indicador_progreso_carga"].active = False
                else:
                    ak.start(cargar_materia(*args))

            cargador_materias = Clock.schedule_interval(iniciar_carga, 0.1)

        if Widget_Principal.activado_pensum:
            cargar_widgets(self)

    def agregar_widgets_pensum(self):
        async def proceso(self):
            self.cargar_pensum = False
            cargador_materias = None
            numero_widget = 0
            iteraciones = self.materias_totales + 10
            lista_widgets_pensum = list(self.diccionario_widgets_pensum.keys())
            menu_pensum_materias = self.ids["menu_pensum_materias"]

            async def cargar_materia(lista, *args):
                nonlocal numero_widget
                await ak.sleep(0)
                try:
                    menu_pensum_materias.add_widget(lista[numero_widget])
                    numero_widget += 1
                except IndexError as e:
                    lista = list(self.diccionario_widgets_pensum.keys())
                    menu_pensum_materias.add_widget(lista[numero_widget])
                    numero_widget += 1

                if numero_widget >= iteraciones:
                    cargador_materias.cancel()

            def iniciar_carga(*args):
                ak.start(cargar_materia(lista_widgets_pensum, *args))

            cargador_materias = Clock.schedule_interval(
                iniciar_carga, self.tiempo_espera
            )

        if Widget_Principal.activado_pensum == False and self.cargar_pensum:
            ak.start(proceso(self))

    def doble_tap(self, instance, touch, materia, es_semestre, semestre=""):
        if touch.is_double_tap:
            if instance.collide_point(*touch.pos):
                if Widget_Principal.ejecucion:
                    Clock.schedule_once(
                        lambda dt, materia=materia, es_semestre=es_semestre, semestre=semestre: self.mostrar_informacion_materia(
                            materia, es_semestre, semestre
                        ),
                        0.5,
                    )
                Widget_Principal.ejecucion = False

    def mostrar_informacion_materia(self, materia_obj, es_semestre, semestre_str):
        if not es_semestre:
            pre1_nombre = "Ninguno"
            pre2_nombre = ""
            pre3_nombre = ""
            coreq_nombre = "Ninguno"
            pre1_codigo = ""
            pre2_codigo = ""
            pre3_codigo = ""
            coreq_codigo = ""
            pre1_semestre = ""
            pre2_semestre = ""
            pre3_semestre = ""
            coreq_semestre = ""

            if materia_obj.pre2 == "U.C.":
                pre1_nombre = f"{materia_obj.pre1} U.C. Aprobadas"
            elif materia_obj.pre1 == "Aprobar todo el pensum":
                pre1_nombre = "Aprobar todo el pensum"
            else:
                if materia_obj.pre1 != "''":
                    m_pre1 = self.buscar_por_codigo(materia_obj.pre1)
                    if m_pre1:
                        pre1_codigo = m_pre1.codigo
                        pre1_nombre = m_pre1.nombre
                        pre1_semestre = f"Semestre:\xa0{m_pre1.semestre}"
                if materia_obj.pre2 != "''":
                    m_pre2 = self.buscar_por_codigo(materia_obj.pre2)
                    if m_pre2:
                        pre2_codigo = m_pre2.codigo
                        pre2_nombre = m_pre2.nombre
                        pre2_semestre = f"Semestre:\xa0{m_pre2.semestre}"
                if materia_obj.pre3 != "''":
                    if self.es_numero(materia_obj.pre3):
                        pre3_nombre = f"{materia_obj.pre3} U.C Aprobadas"
                    else:
                        m_pre3 = self.buscar_por_codigo(materia_obj.pre3)
                        if m_pre3:
                            pre3_codigo = m_pre3.codigo
                            pre3_nombre = m_pre3.nombre
                            pre3_semestre = f"Semestre:\xa0{m_pre3.semestre}"
                if materia_obj.coreq != "''":
                    m_coreq = self.buscar_por_codigo(materia_obj.coreq)
                    if m_coreq:
                        coreq_codigo = m_coreq.codigo
                        coreq_nombre = m_coreq.nombre
                        coreq_semestre = f"Semestre:\xa0{m_coreq.semestre}"

            posreq_str = self.buscar_posreq_str(materia_obj)

            # Casos especiales

            if materia_obj.nombre == "Trabajo Especial I":
                pre3_semestre += "\n\n*Aprobar todas las asignaturas con código EB"

            dialogo_texto = (
                f"[b]{materia_obj.codigo} | {materia_obj.uc}\xa0U.C.[/b]\n"
                f"Horas teóricas: {materia_obj.ht}\nHoras de Aplicación: {materia_obj.ha}\nHoras de laboratorio: {materia_obj.hl}\nHoras Totales: {materia_obj.HT}\n\n"
                f"[b]Pre-requisitos:[/b]\n{pre1_codigo} - {pre1_nombre} - {pre1_semestre}\n"
                f"{pre2_codigo} - {pre2_nombre} - {pre2_semestre}\n"
                f"{pre3_codigo} - {pre3_nombre} - {pre3_semestre}\n\n"
                f"[b]Co-requisitos:[/b]\n{coreq_codigo} - {coreq_nombre} - {coreq_semestre}\n\n"
                f"[b]Requisito para:[/b]\n{posreq_str}"
            )

            dialogo_informacion = MDDialog(
                MDDialogHeadlineText(text=f"{materia_obj.nombre}", halign="center"),
                MDDialogSupportingText(
                    markup=True, text=dialogo_texto, halign="center"
                ),
                size_hint_x=0.9,
                size_hint_y=None,
                radius=dp(15),
                state_press=0,
            )
        else:  # Información del semestre
            unidades_sem = 0
            horas_sem = 0
            unidades_acum = 0
            horas_acum = 0
            cant_materias_sem = 0
            materias_del_semestre_cache = self.get_materias()

            for m_iter in materias_del_semestre_cache:
                if m_iter.semestre == semestre_str:
                    cant_materias_sem += 1
                    unidades_sem += m_iter.uc
                    horas_sem += m_iter.HT

            # Para acumuladas, iterar hasta el semestre anterior al actual
            semestres_orden = [
                "I",
                "II",
                "III",
                "IV",
                "V",
                "VI",
                "VII",
                "VIII",
                "IX",
                "X",
            ]
            try:
                idx_sem_actual = semestres_orden.index(semestre_str)
                semestres_anteriores = semestres_orden[:idx_sem_actual]
                for m_iter_acum in materias_del_semestre_cache:
                    if m_iter_acum.semestre in semestres_anteriores:
                        unidades_acum += m_iter_acum.uc
                        horas_acum += m_iter_acum.HT
                unidades_acum += (
                    unidades_sem  # Añadir las del semestre actual al acumulado
                )
                horas_acum += horas_sem

            except ValueError:
                pass

            dialogo_texto_sem = (
                f"[b]Materias[/b]: {cant_materias_sem}\n"
                f"[b]U.C. Del Semestre[/b]: {unidades_sem}\n"
                f"[b]Horas Totales Del Semestre[/b]: {horas_sem}\n\n"
                f"[b]U.C. Acumuladas[/b]: {unidades_acum}\n"
                f"[b]Horas Totales Acumuladas[/b]: {horas_acum}"
            )

            dialogo_informacion = MDDialog(
                MDDialogHeadlineText(text=f"Semestre {semestre_str}", halign="center"),
                MDDialogSupportingText(
                    markup=True, text=dialogo_texto_sem, halign="center"
                ),
                size_hint_x=0.9,
                size_hint_y=None,
                radius=dp(15),
                state_press=0,
            )

        self._dialogo_info_materia_ref = dialogo_informacion
        boton_cerrar = MDButton(
            MDButtonText(
                text="[b]Cerrar[/b]",
                theme_text_color="Custom",
                text_color=self.CYAN,
                markup=True,
            ),
            on_release=lambda inst: self.cerrar_dialogo(self._dialogo_info_materia_ref),
            style="text",
        )
        container_botones = MDDialogButtonContainer(
            Widget(), boton_cerrar, spacing="8dp"
        )
        dialogo_informacion.add_widget(container_botones)
        dialogo_informacion.open()

        Widget_Principal.ejecucion = True  # Permitir nueva ejecución

    def buscar_posreq_str(self, materia_recibida):
        posreq_lista = []
        lista_materias = self.get_materias()
        for materia in lista_materias:
            if (
                materia.pre1 == materia_recibida.codigo
                or materia.pre2 == materia_recibida.codigo
                or materia.pre3 == materia_recibida.codigo
            ):
                posreq_lista.append(
                    f"{materia.codigo} - {materia.nombre} - Semestre: {materia.semestre}"
                )
        return "\n".join(posreq_lista) if posreq_lista else "Ninguna"

    def buscar_por_codigo(self, codigo):
        if self.materias_dict is None:
            self.get_materias()
        if self.electivas_dict is None:
            self.get_electivas()

        materia = self.materias_dict.get(codigo)
        if materia:
            return materia

        materia_electiva = self.electivas_dict.get(codigo)
        if materia_electiva:
            return materia_electiva

        return None

    def actualizar_pensum(self, codigo):
        lista_materias = self.get_materias()
        r = 0
        while r <= 1:
            for materia in lista_materias:
                if r == 0:
                    # Materia con un solo prerequisito
                    if (
                        materia.pre1 == codigo
                        and materia.pre2 == "''"
                        and materia.coreq == "''"
                    ):
                        materia.disponible = True
                        for clave, valor in self.diccionario_widgets_pensum.items():
                            if valor == materia.codigo:
                                clave.md_bg_color = self.AMARILLO

                    # Materia con dos prerequisitos y sin corequisito
                    elif (materia.pre1 == codigo or materia.pre2 == codigo) and (
                        materia.pre2 != "''"
                        and materia.coreq == "''"
                        and materia.pre3 == "''"
                    ):
                        materia.disponible = True
                        pre1materia = self.buscar_por_codigo(materia.pre1)
                        pre2materia = self.buscar_por_codigo(materia.pre2)

                        if not pre2materia.aprobada or not pre1materia.aprobada:
                            materia.disponible = False
                            disponible = False

                        if materia.disponible:
                            for clave, valor in self.diccionario_widgets_pensum.items():
                                if valor == materia.codigo:
                                    clave.md_bg_color = self.AMARILLO

                    # Materia con 3 requisitos
                    if materia.pre3 != "''" and not materia.aprobada:
                        materia.disponible = True
                        pre1materia = self.buscar_por_codigo(materia.pre1)
                        pre2materia = self.buscar_por_codigo(materia.pre2)
                        pre3 = False
                        if self.es_numero(materia.pre3):
                            if self.unidades_aprobadas >= int(materia.pre3):
                                pre3 = True
                        else:
                            pre3materia = self.buscar_por_codigo(materia.pre3)
                            pre3 = pre3materia.aprobada

                        if (
                            not pre2materia.aprobada
                            or not pre1materia.aprobada
                            or not pre3
                        ):
                            materia.disponible = False

                        if materia.disponible:
                            for clave, valor in self.diccionario_widgets_pensum.items():
                                if valor == materia.codigo:
                                    clave.md_bg_color = self.AMARILLO

                    # Materia con requisito de unidades
                    elif materia.pre2 == "U.C." and not materia.aprobada:
                        if self.unidades_aprobadas >= int(materia.pre1):
                            materia.disponible = True
                            for clave, valor in self.diccionario_widgets_pensum.items():
                                if valor == materia.codigo:
                                    clave.md_bg_color = self.AMARILLO

                    # Entrenamiento industrial
                    elif (
                        materia.pre1 == "Aprobar todo el pensum"
                        and not materia.aprobada
                    ):
                        total = self.materias_totales
                        if self.materias_aprobadas == total - 1:
                            materia.disponible = True
                            for clave, valor in self.diccionario_widgets_pensum.items():
                                if valor == materia.codigo:
                                    clave.md_bg_color = self.AMARILLO
                    # Trabajo Especial I
                    elif (
                        materia.nombre == "Trabajo Especial I" and not materia.aprobada
                    ):
                        if self.materias_basico:
                            pre1materia = self.buscar_por_codigo(materia.pre1)
                            pre2materia = self.buscar_por_codigo(materia.pre2)
                            if pre1materia.aprobada and pre2materia.aprobada:
                                materia.disponible = True
                                for (
                                    clave,
                                    valor,
                                ) in self.diccionario_widgets_pensum.items():
                                    if valor == materia.codigo:
                                        clave.md_bg_color = self.AMARILLO
                        else:
                            materia.disponible = False
                            for clave, valor in self.diccionario_widgets_pensum.items():
                                if valor == materia.codigo:
                                    clave.md_bg_color = self.color_fondo_claro

                # Materia con dos prerequisitos y corequisito
                if (
                    materia.pre1 != "''"
                    and materia.pre2 != "''"
                    and materia.coreq != "''"
                    and not materia.aprobada
                ):
                    pre1materia = self.buscar_por_codigo(materia.pre1)
                    if pre1materia.aprobada:
                        pre2materia = self.buscar_por_codigo(materia.pre2)
                        if pre2materia.aprobada:
                            coreqmateria = self.buscar_por_codigo(materia.coreq)
                            if coreqmateria.disponible:
                                materia.disponible = True
                                for (
                                    clave,
                                    valor,
                                ) in self.diccionario_widgets_pensum.items():
                                    if valor == materia.codigo:
                                        clave.md_bg_color = self.AMARILLO

                # Materia con solo corequisito
                elif (
                    materia.pre1 == "''"
                    and materia.pre2 == "''"
                    and materia.coreq != "''"
                    and not materia.aprobada
                ):
                    coreqmateria = self.buscar_por_codigo(materia.coreq)
                    if coreqmateria.disponible:
                        materia.disponible = True
                        for clave, valor in self.diccionario_widgets_pensum.items():
                            if valor == materia.codigo:
                                clave.md_bg_color = self.AMARILLO

                # Materia con un prerequisito y corequisito
                if (
                    materia.pre1 != "''"
                    and materia.pre2 == "''"
                    and materia.coreq != "''"
                    and not materia.aprobada
                ):
                    pre1materia = self.buscar_por_codigo(materia.pre1)
                    if pre1materia.aprobada:
                        coreqmateria = self.buscar_por_codigo(materia.coreq)
                        if coreqmateria.disponible:
                            materia.disponible = True
                            for clave, valor in self.diccionario_widgets_pensum.items():
                                if valor == materia.codigo:
                                    clave.md_bg_color = self.AMARILLO
            r += 1

    def desactualizar_pensum(self, codigo):
        lista_materias = self.get_materias()
        for materia in lista_materias:
            if materia.aprobada or materia.disponible:
                if (
                    materia.pre1 != "''"
                    and materia.pre2 != "U.C."
                    and materia.pre1 != "Aprobar todo el pensum"
                ):
                    pre1_materia = self.buscar_por_codigo(materia.pre1)
                    pre1 = pre1_materia.aprobada
                else:
                    pre1 = True
                if materia.pre2 != "''" and materia.pre2 != "U.C.":
                    pre2_materia = self.buscar_por_codigo(materia.pre2)
                    pre2 = pre2_materia.aprobada
                else:
                    pre2 = True
                if materia.pre3 != "''":
                    if self.es_numero(materia.pre3):
                        if int(self.unidades_aprobadas) < int(materia.pre3):
                            pre3 = False
                    else:
                        pre3_materia = self.buscar_por_codigo(materia.pre3)
                        pre3 = pre3_materia.aprobada
                else:
                    pre3 = True

                if materia.coreq != "''":
                    coreq_materia = self.buscar_por_codigo(materia.coreq)
                    coreq = coreq_materia.disponible
                else:
                    coreq = True

                if materia.pre2 == "U.C.":
                    if int(self.unidades_aprobadas) < int(materia.pre1):
                        req_unidades = False
                else:
                    req_unidades = True

                if materia.nombre == "Trabajo Especial I":
                    if not self.materias_basico:
                        req_basico = False
                else:
                    req_basico = True

                if materia.pre1 == "Aprobar todo el pensum":
                    total = self.materias_totales

                    if self.materias_aprobadas < (total - 1) and not materia.aprobada:
                        req_entrenamiento_industrial = False
                    elif materia.aprobada:
                        if (self.materias_aprobadas - 1) <= (total - 1):
                            req_entrenamiento_industrial = False
                else:
                    req_entrenamiento_industrial = True

                if (
                    not pre1
                    or not pre2
                    or not pre3
                    or not coreq
                    or not req_unidades
                    or not req_basico
                    or not req_entrenamiento_industrial
                ):
                    materia.aprobada = False
                    materia.disponible = False
                    for clave, valor in self.diccionario_widgets_pensum.items():
                        if valor == materia.codigo:
                            clave.md_bg_color = self.color_fondo_claro
                    for clave, valor in self.diccionario_checkboxs_pensum.items():
                        if valor == materia.codigo:
                            clave.active = False

    @auto_save_materias
    def aprobar_materia(self, checkbox, value, codigo, objeto_lista):
        materia = self.buscar_por_codigo(codigo)

        if value:
            if materia.disponible:
                materia.aprobada = True
                self.unidades_aprobadas_y_totales()
                self.actualizar_pensum(materia.codigo)
                objeto_lista.md_bg_color = self.VERDE
            else:
                checkbox.active = False
        else:
            if materia.disponible:
                materia.aprobada = False
                objeto_lista.md_bg_color = self.AMARILLO
                self.unidades_aprobadas_y_totales()
                self.desactualizar_pensum(materia.codigo)

            else:
                materia.aprobada = False
                self.unidades_aprobadas_y_totales()
                objeto_lista.md_bg_color = self.color_fondo_claro

    def unidades_aprobadas_y_totales(self):
        lista_materias = self.get_materias()
        self.materias_totales = len(lista_materias)
        self.unidades_aprobadas = 0
        self.unidades_totales = 0
        self.materias_aprobadas = 0

        # Materias inscritas
        self.unidades_inscritas = 0
        self.lista_materias_inscritas = []

        # Materias para inscribir
        self.old_lista_materias_para_inscribir = self.lista_materias_para_inscribir[:]
        self.lista_materias_para_inscribir = []
        self.unidades_para_inscribir = 0

        self.materias_basico = True
        for materia in lista_materias:
            if "EB" in materia.codigo:
                if not materia.aprobada:
                    self.materias_basico = False
            self.unidades_totales += materia.uc
            if materia.aprobada:
                self.unidades_aprobadas += materia.uc
                self.materias_aprobadas += 1
            if (
                materia.disponible
                and not materia.aprobada
                and materia.nombre != "Electiva Profesional I"
                and materia.nombre != "Electiva Profesional II"
                and materia.nombre != "Electiva Profesional III"
                and materia.nombre != "Electiva Profesional IV"
            ):
                self.unidades_para_inscribir += materia.uc
                self.lista_materias_para_inscribir.append(materia)
            if materia.inscrita:
                self.lista_materias_inscritas.append(materia)
                self.unidades_inscritas += materia.uc

        if self.texto_mencion == "No Aplica":
            self.texto_mencion_label = " "
        else:
            self.texto_mencion_label = f" | {self.texto_mencion}"
        self.porcentaje_aprobadas = (
            self.materias_aprobadas * 100 / self.materias_totales
        )
        self.porcentaje_uc_aprobadas = (
            self.unidades_aprobadas * 100 / self.unidades_totales
        )

        if self.unidades_aprobadas <= 18:
            self.semestre_actual = "I"
        elif self.unidades_aprobadas <= 36:
            self.semestre_actual = "II"
        elif self.unidades_aprobadas <= 55:
            self.semestre_actual = "III"
        elif self.unidades_aprobadas <= 75:
            self.semestre_actual = "IV"
        elif self.unidades_aprobadas <= 94:
            self.semestre_actual = "V"
        elif self.unidades_aprobadas <= 113:
            self.semestre_actual = "VI"
        elif self.unidades_aprobadas <= 128:
            self.semestre_actual = "VII"
        elif self.unidades_aprobadas <= 146:
            self.semestre_actual = "VIII"
        elif self.unidades_aprobadas <= 161:
            self.semestre_actual = "IX"
        else:
            self.semestre_actual = "X"

    def mostrar_guia_pensum(self, *args):
        if self.guia_pensum:
            dialogo_informacion = MDDialog(
                MDDialogIcon(
                    icon="information",
                    theme_icon_color="Custom",
                    icon_color=self.AZUL_CLARO,
                ),
                MDDialogHeadlineText(text="[b]Guía de [i]Pensum[/i][/b]"),
                MDDialogSupportingText(
                    text="Código de colores:\n\n [b]Sin color[/b]: No cumples con los requisitos para ver la materia.\n\n[color=#FFD700][b]Amarillo[/b][/color]: Cumples con los requisitos para ver la materia.\n\n[color=#00FF00][b]Verde[/b][/color]: Materia aprobada.\n\n*Nota: Toca dos veces en una materia o semestre para ver la información completa.",
                    markup=True,
                    halign="left",
                ),
                size_hint_x=0.9,
                size_hint_y=None,
                radius=[dp(10), dp(10), dp(10), dp(10)],
                ripple_duration_in_fast=0,
                ripple_duration_in_slow=0,
                theme_focus_color="Custom",
                focus_color=[1, 1, 1, 0],
                padding="0dp",
                state_press=0,
            )
            boton = MDDialogButtonContainer(
                Widget(),
                MDButton(
                    MDButtonText(
                        text="[b]Ok[/b]",
                        theme_text_color="Custom",
                        text_color=self.CYAN,
                        markup=True,
                    ),
                    on_release=lambda instance, dialogo=dialogo_informacion: self.cerrar_dialogo(
                        dialogo
                    ),
                    style="text",
                ),
            )
            dialogo_informacion.add_widget(boton)
            dialogo_informacion.open()
            self.guia_pensum = False

    def acceso_directo_electivas(self):
        dialogo_advertencia = MDDialog(
            MDDialogIcon(
                icon="information",
                theme_icon_color="Custom",
                icon_color=self.AZUL_CLARO,
            ),
            MDDialogHeadlineText(text="Ver Electivas"),
            MDDialogSupportingText(
                text="Ir a la sección de configuración->electivas", halign="left"
            ),
            size_hint_x=0.9,
            size_hint_y=None,
            radius=[dp(10), dp(10), dp(10), dp(10)],
            ripple_duration_in_fast=0,
            ripple_duration_in_slow=0,
            theme_focus_color="Custom",
            focus_color=[1, 1, 1, 0],
            padding="0dp",
            state_press=0,
        )
        botones = MDDialogButtonContainer(
            Widget(),
            MDButton(
                MDButtonText(
                    text="[b]Cancelar[/b]",
                    theme_text_color="Custom",
                    text_color=self.CYAN,
                    markup=True,
                ),
                on_release=lambda instance, dialogo=dialogo_advertencia: self.cerrar_dialogo(
                    dialogo
                ),
                style="text",
            ),
            MDButton(
                MDButtonText(
                    text="[b]Aceptar[/b]",
                    theme_text_color="Custom",
                    text_color=self.CYAN,
                    markup=True,
                ),
                on_release=lambda instance, x=dialogo_advertencia: self.ir_a_electivas(
                    instance, x
                ),
                style="text",
            ),
            spacing="8dp",
        )
        dialogo_advertencia.add_widget(botones)
        dialogo_advertencia.open()

    def ir_a_electivas(self, instance, dialogo):
        dialogo.dismiss()
        self.transition = SlideTransition(direction="down")
        if not self.has_screen("Configuracion"):
            self.add_widget(Configuracion())
            pantalla_configuracion = self.get_screen("Configuracion")
            pantalla_configuracion.tiempo_espera = self.texto_tiempo_espera
            pantalla_configuracion.tema = self.tema

        self.current = "Configuracion"
        self.abrir_menu_electivas()
        self.transition = SlideTransition(direction="right")

    # Configuración electivas
    def abrir_menu_electivas(self):
        async def carga_asincrona(*args):
            lista_electivas = self.get_electivas()
            lista_materias = self.get_materias()
            lista_materias_codigos = [materia.codigo for materia in lista_materias]
            box_layout = MDBoxLayout(
                size_hint_y=None,
                height=dp(len(lista_electivas) * 100),
                orientation="vertical",
            )
            scrollview = MDScrollView(
                box_layout, size_hint_y=None, height=dp(280), bar_width=0
            )
            self.contador_electivas = 0

            for electiva in lista_electivas:
                await ak.sleep(0)
                pre1 = self.buscar_por_codigo(electiva.pre1)

                if electiva.pre2 != "''":
                    pre2a = self.buscar_por_codigo(electiva.pre2)
                    pre2 = f"\nPrereq. 2: {pre2a.nombre}"
                else:
                    pre2 = ""

                check_box = MDCheckbox(
                    id=electiva.nombre,
                    color_inactive="gray",
                    color_active=self.CYAN,
                    pos_hint={"center_x": 0.9, "center_y": 0.5},
                )
                objeto_lista = BoxConRipplePensum(
                    LabelListaPensum(
                        text=f"[b][size=14sp]{electiva.nombre}[/size][/b]\n[size=12sp][color={('#B2B2B2' if self.tema=='Oscuro' else '#333333')}]Prereq. 1: {pre1.nombre}{pre2}[/color][/size]"
                    ),
                    check_box,
                    theme_bg_color="Custom",
                    md_bg_color=self.color_fondo_claro,
                    height=dp(100),
                )

                # Electivas que ya están en la lista de materias
                if electiva.codigo in lista_materias_codigos:
                    if electiva.semestre != "Opcional":
                        self.contador_electivas += 1
                    else:
                        self.contador_electivas += 2
                    check_box.active = True

                check_box.bind(
                    active=lambda checkbox, value, electiva=electiva, objeto_lista=objeto_lista: self.gestionar_electiva(
                        checkbox, value, electiva, objeto_lista
                    )
                )
                objeto_lista.bind(
                    on_touch_down=lambda instance, touch, electiva=electiva, es_semestre=False: self.doble_tap(
                        instance, touch, electiva, es_semestre
                    )
                )
                box_layout.add_widget(objeto_lista)

            menu_seleccion = MDDialog(
                MDDialogIcon(
                    icon="information",
                    theme_icon_color="Custom",
                    icon_color=self.AZUL_CLARO,
                ),
                MDDialogHeadlineText(text="Seleccionar electivas"),
                MDDialogSupportingText(
                    text="Selecciona las electivas para Índice y Pensum\n\n*El orden de selección es tomado en cuenta para ubicarlas en el semestre correspondiente.",
                    halign="left",
                ),
                MDDialogContentContainer(
                    MDDivider(), scrollview, MDDivider(), orientation="vertical"
                ),
                size_hint_x=0.9,
                radius=dp(10),
                ripple_scale=0,
                theme_focus_color="Custom",
                padding="0dp",
                hide_duration=0.5,
                state_press=0,
            )
            boton_aceptar = MDDialogButtonContainer(
                Widget(),
                MDButton(
                    MDButtonText(
                        text="[b]Aceptar[/b]",
                        theme_text_color="Custom",
                        text_color=self.CYAN,
                        markup=True,
                    ),
                    on_release=lambda instance, dialogo=menu_seleccion: self.cerrar_dialogo(
                        dialogo
                    ),
                    style="text",
                ),
            )
            boton_ir_pensum = MDDialogButtonContainer(
                Widget(),
                MDButton(
                    MDButtonText(
                        text="[b]Ir a Pensum[/b]",
                        theme_text_color="Custom",
                        text_color=self.CYAN,
                        markup=True,
                    ),
                    on_release=lambda instance, dialogo=menu_seleccion: self.ir_al_pensum(
                        dialogo
                    ),
                    style="text",
                ),
            )
            menu_seleccion.add_widget(boton_ir_pensum)
            menu_seleccion.add_widget(boton_aceptar)
            menu_seleccion.open()

        ak.start(carga_asincrona(self))

    def cerrar_dialogo(self, dialogo):
        dialogo.dismiss()

    def ir_al_pensum(self, dialogo):
        dialogo.dismiss()
        self.transition = SlideTransition(direction="up")
        self.mostrar_materias_inicio()
        self.cargar_widget_pensum()
        self.cargar_widget_notas()
        Clock.schedule_once(lambda dt: self.agregar_widgets_pensum(), 1)
        self.current = "Pensum"
        self.pensum_active = True
        self.inicio_active = False
        self.notas_active = False
        self.horario_active = False

    @auto_save_materias
    def gestionar_electiva(self, checkbox, value, electiva, objeto_lista):
        def reemplazar_en_indice(materia_a_reemplazar, objeto_add, campo_add):
            campo_a_eliminar = None
            for objeto in self.widgets_lista_notas:
                if objeto.id == f"{materia_a_reemplazar.codigo}WN":
                    objeto_a_eliminar = objeto
                    for campo in self.lista_campos:
                        if campo.id == f"{materia_a_reemplazar.codigo}WCT":
                            campo_a_eliminar = campo

            # Reemplazarlo si ya estaba cargado, si no solo se añadir a la lista
            if self.cargar_indice == False:
                indice = self.ids["menu_notas_materias"].children.index(
                    objeto_a_eliminar
                )
                self.ids["menu_notas_materias"].remove_widget(objeto_a_eliminar)
                self.ids["menu_notas_materias"].add_widget(objeto_add, indice)

            indice = self.lista_campos.index(campo_a_eliminar)
            self.lista_campos[indice] = campo_add
            indice = self.widgets_lista_notas.index(objeto_a_eliminar)
            self.widgets_lista_notas[indice] = objeto_add

        def reemplazar_en_pensum(materia_a_reemplazar, objeto_add, materia_add):
            objeto_a_eliminar = None
            check_a_eliminar = None

            for objeto, codigo_materia in self.diccionario_widgets_pensum.items():
                if codigo_materia == materia_a_reemplazar.codigo:
                    objeto_a_eliminar = objeto
                    for check, codigo in self.diccionario_checkboxs_pensum.items():
                        if codigo == materia_a_reemplazar.codigo:
                            check_a_eliminar = check

            # Si se cargó el pensum se reemplaza, si no se añade a la lista
            if self.cargar_pensum == False:
                indice = self.ids["menu_pensum_materias"].children.index(
                    objeto_a_eliminar
                )
                self.ids["menu_pensum_materias"].remove_widget(objeto_a_eliminar)
                self.ids["menu_pensum_materias"].add_widget(objeto_add, indice)

            del self.diccionario_checkboxs_pensum[check_a_eliminar]
            self.diccionario_widgets_pensum = {
                (objeto_add if k == objeto_a_eliminar else k): v
                for k, v in self.diccionario_widgets_pensum.items()
            }
            self.diccionario_widgets_pensum[objeto_add] = materia_add.codigo

        lista_materias = self.get_materias()
        lista_materias_codigos = [materia.semestre for materia in lista_materias]
        entrenamiento_industrial_opcional = 0
        if "Opcional" in lista_materias_codigos:
            entrenamiento_industrial_opcional = 1

        max_electivas = 3
        if self.texto_especialidad == "Ing. Industrial":
            max_electivas = 2
            indices_electivas = [49, 55]
        elif self.texto_especialidad == "Ing. Eléctrica":
            max_electivas = 4
            indices_electivas = [49, 50, 54, 55]
        elif (
            self.texto_especialidad == "Ing. Electrónica"
            and not self.texto_mencion == "Comunicaciones"
        ):
            indices_electivas = [51, 56, 57]
        elif (
            self.texto_especialidad == "Ing. Electrónica"
            and self.texto_mencion == "Comunicaciones"
        ):
            indices_electivas = [55, 56, 57]
        elif self.texto_especialidad == "Ing. Mecánica":
            indices_electivas = [52, 53, 54]
        elif self.texto_especialidad == "Ing. Metalúrgica":
            indices_electivas = [49, 54, 55]
        elif self.texto_especialidad == "Ing. Química":
            indices_electivas = [51, 55, 56]

        if value:
            if electiva.semestre != "Opcional":
                if self.contador_electivas + 1 > max_electivas:
                    MDSnackbar(
                        MDSnackbarText(
                            text=f"Solo puedes añadir hasta {max_electivas} electivas."
                        ),
                        MDSnackbarSupportingText(
                            text="Deselecciona una y vuelve a intentar."
                        ),
                        pos_hint={"center_x": 0.5},
                        size_hint_x=0.8,
                        orientation="horizontal",
                        y=dp(10),
                    ).open()
                    self.contador_electivas += 1
                    checkbox.active = False
                else:
                    materia_a_reemplazar = lista_materias[
                        indices_electivas[self.contador_electivas]
                        - entrenamiento_industrial_opcional
                    ]
                    lista_materias[
                        indices_electivas[self.contador_electivas]
                        - entrenamiento_industrial_opcional
                    ] = electiva

                    pre1 = self.buscar_por_codigo(electiva.pre1)

                    if electiva.pre2 != "''":
                        pre2 = self.buscar_por_codigo(electiva.pre2)
                        req_pre2 = pre2.aprobada
                    else:
                        req_pre2 = True

                    if electiva.coreq != "''":
                        coreq = self.buscar_por_codigo(electiva.coreq)
                        req_coreq = coreq.disponible
                    else:
                        req_coreq = True

                    if pre1.aprobada and req_pre2 and req_coreq:
                        electiva.disponible = True

                    self.desactualizar_pensum("codigo")
                    self.unidades_aprobadas_y_totales()

                    self.contador_electivas += 1

                    # Crear widget a reemplazar en el pensum o en el diccionario

                    check_box = CheckBoxPensum(id=electiva.codigo)
                    objeto_lista = objeto_add = BoxConRipplePensum(
                        LabelListaPensum(
                            text=f"[b]{electiva.nombre}\n[size=14sp][color={('#B2B2B2' if self.tema=='Oscuro' else '#333333')}]Código: {electiva.codigo}[/b]\n{electiva.uc} U.C[/color][/size]"
                        ),
                        check_box,
                        id=f"{electiva.codigo}WP",
                        theme_bg_color="Custom",
                        md_bg_color=self.color_fondo_claro,
                    )

                    if electiva.disponible:
                        objeto_lista.md_bg_color = self.AMARILLO
                    else:
                        objeto_lista.md_bg_color = self.color_fondo_claro

                    check_box.bind(
                        active=lambda checkbox, value, codigo=electiva.codigo, objeto_lista=objeto_lista: self.aprobar_materia(
                            checkbox, value, codigo, objeto_lista
                        )
                    )
                    self.diccionario_checkboxs_pensum[check_box] = electiva.codigo
                    objeto_lista.bind(
                        on_touch_down=lambda instance, touch, electiva=electiva, es_semestre=False: self.doble_tap(
                            instance, touch, electiva, es_semestre
                        )
                    )

                    reemplazar_en_pensum(materia_a_reemplazar, objeto_add, electiva)

                    # Crear widget de indice
                    campo_texto = campo_add = CampoTextoListaIndice(
                        id=f"{electiva.codigo}WCT",
                        text=str(electiva.nota).replace("''", ""),
                        max_height="35dp",
                    )
                    objeto_lista = objeto_add = BoxConRippleIndice(
                        LabelListaIndice(
                            text=f"[b]{electiva.nombre}[/b]\n[size=14sp]{electiva.uc} U.C[/size]"
                        ),
                        campo_texto,
                        id=f"{electiva.codigo}WN",
                    )
                    campo_texto.bind(
                        focus=lambda instance, value, codigo=electiva.codigo: self.on_focus(
                            instance, value, codigo
                        ),
                        on_text_validate=self.siguiente_campo_notas,
                    )
                    objeto_lista.bind(
                        on_touch_down=lambda instance, touch, m=electiva: self.ver_evaluaciones(
                            instance, touch, m, True
                        )
                    )
                    reemplazar_en_indice(materia_a_reemplazar, objeto_add, campo_add)

            else:
                # Entrenamiento industrial opcional
                if self.contador_electivas + 2 > max_electivas:
                    MDSnackbar(
                        MDSnackbarText(
                            text=f"Solo puedes añadir hasta {max_electivas} electivas."
                        ),
                        MDSnackbarSupportingText(
                            text="El entrenamiento industrial opcional se realiza en reemplazo de 2 electivas."
                        ),
                        pos_hint={"center_x": 0.5},
                        size_hint_x=0.8,
                        orientation="horizontal",
                        y=dp(10),
                    ).open()
                    self.contador_electivas += 1
                    checkbox.active = False
                else:
                    materia_a_reemplazar = lista_materias[
                        indices_electivas[self.contador_electivas]
                    ]
                    lista_materias[
                        indices_electivas[self.contador_electivas]
                    ] = electiva
                    materia_a_eliminar = lista_materias[
                        indices_electivas[self.contador_electivas + 1]
                    ]
                    lista_materias.pop(indices_electivas[self.contador_electivas + 1])

                    pre1 = self.buscar_por_codigo(electiva.pre1)

                    if electiva.pre2 != "''":
                        pre2 = self.buscar_por_codigo(electiva.pre2)
                        req_pre2 = pre2.aprobada
                    else:
                        req_pre2 = True

                    if electiva.pre3 != "''":
                        pre3 = self.buscar_por_codigo(electiva.pre2)
                        req_pre3 = pre3.aprobada
                    else:
                        req_pre3 = True

                    if electiva.coreq != "''":
                        coreq = self.buscar_por_codigo(electiva.coreq)
                        req_coreq = coreq.disponible
                    else:
                        req_coreq = True

                    if pre1.aprobada and req_pre2 and req_pre3 and req_coreq:
                        electiva.disponible = True

                    self.desactualizar_pensum("codigo")
                    self.unidades_aprobadas_y_totales()

                    self.contador_electivas += 2

                    # Crear widget a reemplazar en el pensum o en el diccionario

                    check_box = CheckBoxPensum(id=electiva.codigo)
                    objeto_lista = objeto_add = BoxConRipplePensum(
                        LabelListaPensum(
                            text=f"[b]{electiva.nombre}\n[size=14sp][color={('#B2B2B2' if self.tema=='Oscuro' else '#333333')}]Código: {electiva.codigo}[/b]\n{electiva.uc} U.C[/color][/size]"
                        ),
                        check_box,
                        id=f"{electiva.codigo}WP",
                        theme_bg_color="Custom",
                        md_bg_color=self.color_fondo_claro,
                    )

                    if electiva.disponible:
                        objeto_lista.md_bg_color = self.AMARILLO
                    else:
                        objeto_lista.md_bg_color = self.color_fondo_claro

                    check_box.bind(
                        active=lambda checkbox, value, codigo=electiva.codigo, objeto_lista=objeto_lista: self.aprobar_materia(
                            checkbox, value, codigo, objeto_lista
                        )
                    )
                    self.diccionario_checkboxs_pensum[check_box] = electiva.codigo
                    objeto_lista.bind(
                        on_touch_down=lambda instance, touch, electiva=electiva, es_semestre=False: self.doble_tap(
                            instance, touch, electiva, es_semestre
                        )
                    )

                    # Identificar widgets en el diccionario
                    objeto_a_eliminar = []
                    check_a_eliminar = []
                    for materia in [materia_a_reemplazar, materia_a_eliminar]:
                        for (
                            objeto,
                            codigo_materia,
                        ) in self.diccionario_widgets_pensum.items():
                            if codigo_materia == materia.codigo:
                                objeto_a_eliminar.append(objeto)
                                for (
                                    check,
                                    codigo,
                                ) in self.diccionario_checkboxs_pensum.items():
                                    if codigo == materia.codigo:
                                        check_a_eliminar.append(check)

                    # Si se cargó el pensum se reemplaza, si no se añade a la lista
                    if self.cargar_pensum == False:
                        indice = self.ids["menu_pensum_materias"].children.index(
                            objeto_a_eliminar[0]
                        )
                        self.ids["menu_pensum_materias"].remove_widget(
                            objeto_a_eliminar[0]
                        )
                        self.ids["menu_pensum_materias"].add_widget(
                            objeto_lista, indice
                        )
                        self.ids["menu_pensum_materias"].remove_widget(
                            objeto_a_eliminar[1]
                        )

                    del self.diccionario_checkboxs_pensum[check_a_eliminar[0]]
                    del self.diccionario_checkboxs_pensum[check_a_eliminar[1]]
                    del self.diccionario_widgets_pensum[objeto_a_eliminar[1]]
                    self.diccionario_widgets_pensum = {
                        (objeto_add if k == objeto_a_eliminar[0] else k): v
                        for k, v in self.diccionario_widgets_pensum.items()
                    }
                    self.diccionario_widgets_pensum[objeto_add] = electiva.codigo

                    # Crear widget de indice
                    campo_texto = campo_add = CampoTextoListaIndice(
                        id=f"{electiva.codigo}WCT",
                        text=str(electiva.nota).replace("''", ""),
                        max_height="35dp",
                    )
                    objeto_lista = objeto_add = BoxConRippleIndice(
                        LabelListaIndice(
                            text=f"[b]{electiva.nombre}[/b]\n[size=14sp]{electiva.uc} U.C[/size]"
                        ),
                        campo_texto,
                        id=f"{electiva.codigo}WN",
                    )
                    campo_texto.bind(
                        focus=lambda instance, value, codigo=electiva.codigo: self.on_focus(
                            instance, value, codigo
                        ),
                        on_text_validate=self.siguiente_campo_notas,
                    )
                    objeto_lista.bind(
                        on_touch_down=lambda instance, touch, m=electiva: self.ver_evaluaciones(
                            instance, touch, m, True
                        )
                    )

                    campo_a_eliminar = []
                    objeto_a_eliminar = []
                    for materia in [materia_a_reemplazar, materia_a_eliminar]:
                        for objeto in self.widgets_lista_notas:
                            if objeto.id == f"{materia.codigo}WN":
                                objeto_a_eliminar.append(objeto)
                                for campo in self.lista_campos:
                                    if campo.id == f"{materia.codigo}WCT":
                                        campo_a_eliminar.append(campo)

                    # Reemplazarlo si ya estaba cargado, si no solo se añadir a la lista
                    if self.cargar_indice == False:
                        indice = self.ids["menu_notas_materias"].children.index(
                            objeto_a_eliminar[0]
                        )
                        self.ids["menu_notas_materias"].remove_widget(
                            objeto_a_eliminar[0]
                        )
                        self.ids["menu_notas_materias"].add_widget(objeto_lista, indice)
                        self.ids["menu_notas_materias"].remove_widget(
                            objeto_a_eliminar[1]
                        )

                    indice = self.lista_campos.index(campo_a_eliminar[0])
                    self.lista_campos[indice] = campo_add
                    indice = self.widgets_lista_notas.index(objeto_a_eliminar[0])
                    self.widgets_lista_notas[indice] = objeto_add
                    self.lista_campos.remove(campo_a_eliminar[1])
                    self.widgets_lista_notas.remove(objeto_a_eliminar[1])

        else:
            if electiva not in lista_materias:
                self.contador_electivas -= 1
            else:
                # Crear widget a reemplazar en el indice

                codigos_defecto = [
                    "Según Materia I",
                    "Según Materia II",
                    "Según Materia III",
                    "Según Materia IV",
                ]
                nombres_defecto = [
                    "Electiva Profesional I",
                    "Electiva Profesional II",
                    "Electiva Profesional III",
                    "Electiva Profesional IV",
                ]

                entrenamiento_industrial_opcional = 0
                if (
                    "Opcional"
                    in lista_materias_codigos[: lista_materias.index(electiva)]
                ):
                    entrenamiento_industrial_opcional = 1
                indice = lista_materias.index(electiva)
                if electiva.semestre != "Opcional":
                    indice += entrenamiento_industrial_opcional
                numero_electiva = indices_electivas.index(indice)
                if indice <= 50:
                    semestre = "VIII"
                else:
                    semestre = "IX"

                electiva_defecto = Materia(
                    semestre,
                    codigos_defecto[numero_electiva],
                    nombres_defecto[numero_electiva],
                    3,
                    0,
                    0,
                    3,
                    "''",
                    False,
                    False,
                    "''",
                    "''",
                    "''",
                )

                campo_texto = campo_add = CampoTextoListaIndice(
                    id=f"{electiva_defecto.codigo}WCT",
                    text=str(electiva_defecto.nota).replace("''", ""),
                    max_height="35dp",
                )
                objeto_lista = objeto_add = BoxConRippleIndice(
                    LabelListaIndice(
                        text=f"[b]{electiva_defecto.nombre}[/b]\n[size=14sp]{electiva_defecto.uc} U.C[/size]"
                    ),
                    campo_texto,
                    id=f"{electiva_defecto.codigo}WN",
                )
                campo_texto.bind(
                    focus=lambda instance, value, codigo=electiva_defecto.codigo: self.on_focus(
                        instance, value, codigo
                    ),
                    on_text_validate=self.siguiente_campo_notas,
                )

                if electiva.semestre != "Opcional":
                    indice -= entrenamiento_industrial_opcional
                lista_materias[indice] = electiva_defecto

                reemplazar_en_indice(electiva, objeto_add, campo_add)

                # Crear widget a reemplazar en pensum
                check_box = CheckBoxPensum(id=electiva_defecto.codigo)
                objeto_lista = objeto_add = BoxConRipplePensum(
                    LabelListaPensum(
                        text=f"[b]{electiva_defecto.nombre}\n[size=14sp][color={('#B2B2B2' if self.tema=='Oscuro' else '#333333')}]Código: {electiva_defecto.codigo}[/b]\n{electiva_defecto.uc} U.C[/color][/size]"
                    ),
                    check_box,
                    id=f"{electiva_defecto.codigo}WP",
                    theme_bg_color="Custom",
                    md_bg_color=self.color_fondo_claro,
                )

                if electiva_defecto.disponible:
                    objeto_lista.md_bg_color = self.AMARILLO
                else:
                    objeto_lista.md_bg_color = self.color_fondo_claro

                check_box.bind(
                    active=lambda checkbox, value, codigo=electiva_defecto.codigo, objeto_lista=objeto_lista: self.aprobar_materia(
                        checkbox, value, codigo, objeto_lista
                    )
                )
                self.diccionario_checkboxs_pensum[check_box] = electiva_defecto.codigo
                objeto_lista.bind(
                    on_touch_down=lambda instance, touch, electiva_defecto=electiva_defecto, es_semestre=False: self.doble_tap(
                        instance, touch, electiva_defecto, es_semestre
                    )
                )

                reemplazar_en_pensum(electiva, objeto_add, electiva_defecto)

                self.contador_electivas -= 1

                if electiva.semestre == "Opcional":
                    numero_electiva += 1
                    indice = indices_electivas[numero_electiva]
                    if indice <= 50:
                        semestre = "VIII"
                    else:
                        semestre = "IX"

                    # Crear materia y widget extra para el indice
                    electiva_defecto = Materia(
                        semestre,
                        codigos_defecto[numero_electiva],
                        nombres_defecto[numero_electiva],
                        3,
                        0,
                        0,
                        3,
                        "''",
                        False,
                        False,
                        "''",
                        "''",
                        "''",
                    )

                    campo_texto = campo_add = CampoTextoListaIndice(
                        id=f"{electiva_defecto.codigo}WCT",
                        text=str(electiva_defecto.nota).replace("''", ""),
                        max_height="35dp",
                    )
                    objeto_lista = objeto_add = BoxConRippleIndice(
                        LabelListaIndice(
                            text=f"[b]{electiva_defecto.nombre}[/b]\n[size=14sp]{electiva_defecto.uc} U.C[/size]"
                        ),
                        campo_texto,
                        id=f"{electiva_defecto.codigo}WN",
                    )
                    campo_texto.bind(
                        focus=lambda instance, value, codigo=electiva_defecto.codigo: self.on_focus(
                            instance, value, codigo
                        ),
                        on_text_validate=self.siguiente_campo_notas,
                    )

                    lista_materias.insert(indice, electiva_defecto)
                    widgets_semestre = 1 if semestre == "IX" else 2
                    posicion = len(lista_materias) - indice - 1 + widgets_semestre

                    # Añadir widget extra en indice
                    if self.cargar_indice == False:
                        self.ids["menu_notas_materias"].add_widget(objeto_add, posicion)

                    self.lista_campos.insert(indice, campo_add)
                    self.widgets_lista_notas.insert(
                        indice + 10 - widgets_semestre, objeto_add
                    )

                    # Crear materia y widget extra para el pensum
                    check_box = CheckBoxPensum(id=electiva_defecto.codigo)
                    objeto_lista = objeto_add = BoxConRipplePensum(
                        LabelListaPensum(
                            text=f"[b]{electiva_defecto.nombre}\n[size=14sp][color={('#B2B2B2' if self.tema=='Oscuro' else '#333333')}]Código: {electiva_defecto.codigo}[/b]\n{electiva_defecto.uc} U.C[/color][/size]"
                        ),
                        check_box,
                        id=f"{electiva_defecto.codigo}WP",
                        theme_bg_color="Custom",
                        md_bg_color=self.color_fondo_claro,
                    )

                    if electiva_defecto.disponible:
                        objeto_lista.md_bg_color = self.AMARILLO
                    else:
                        objeto_lista.md_bg_color = self.color_fondo_claro

                    check_box.bind(
                        active=lambda checkbox, value, codigo=electiva_defecto.codigo, objeto_lista=objeto_lista: self.aprobar_materia(
                            checkbox, value, codigo, objeto_lista
                        )
                    )
                    self.diccionario_checkboxs_pensum[
                        check_box
                    ] = electiva_defecto.codigo
                    objeto_lista.bind(
                        on_touch_down=lambda instance, touch, electiva_defecto=electiva_defecto, es_semestre=False: self.doble_tap(
                            instance, touch, electiva_defecto, es_semestre
                        )
                    )

                    # Añadir widget extra en pensum
                    if self.cargar_pensum == False:
                        self.ids["menu_pensum_materias"].add_widget(
                            objeto_add, posicion
                        )

                    items = list(self.diccionario_widgets_pensum.items())
                    items.insert(
                        indice + 10 - widgets_semestre,
                        (objeto_add, electiva_defecto.codigo),
                    )
                    self.diccionario_widgets_pensum = dict(items)

                    self.contador_electivas -= 1
                    self.desactualizar_pensum("codigo")
                    self.unidades_aprobadas_y_totales()

    def reiniciar_widgets(self):
        if Widget_Principal.activado_pensum == False:
            self.ids["menu_pensum_materias"].clear_widgets()
            self.diccionario_widgets_pensum = {}
            self.diccionario_checkboxs_pensum = {}
            Widget_Principal.activado_pensum = True
            self.cargar_pensum = True

        if Widget_Principal.activado == False:
            self.ids["menu_notas_materias"].clear_widgets()
            self.widgets_lista_notas = []
            self.lista_campos = []
            Widget_Principal.activado = True
            self.cargar_indice = True

        if self.has_screen("Horario"):
            self.get_screen("Horario").ids["contenedor_horario"].clear_widgets()

    # Configuración-Cambio especialidad
    def advertencia_cambio_especialidad(self):
        dialogo_advertencia = MDDialog(
            MDDialogIcon(
                icon="information",
                theme_icon_color="Custom",
                icon_color=self.AZUL_OSCURO,
            ),
            MDDialogHeadlineText(text="¡Importante! "),
            MDDialogSupportingText(
                text="Al presionar aceptar volverás a la pantalla de selección de especialidad y mención. Los datos de la actual especialidad no serán borrados y podrás volver a ellos seleccionando la misma especialidad y mención.",
                halign="left",
            ),
            size_hint_x=0.9,
            size_hint_y=None,
            radius=[dp(10), dp(10), dp(10), dp(10)],
            ripple_duration_in_fast=0,
            ripple_duration_in_slow=0,
            theme_focus_color="Custom",
            focus_color=[1, 1, 1, 0],
            padding="0dp",
            state_press=0,
        )
        botones = MDDialogButtonContainer(
            Widget(),
            MDButton(
                MDButtonText(
                    text="[b]Cancelar[/b]",
                    theme_text_color="Custom",
                    text_color=self.CYAN,
                    markup=True,
                ),
                on_release=lambda instance, dialogo=dialogo_advertencia: self.cerrar_dialogo(
                    dialogo
                ),
                style="text",
            ),
            MDButton(
                MDButtonText(
                    text="[b]Aceptar[/b]",
                    theme_text_color="Custom",
                    text_color=self.CYAN,
                    markup=True,
                ),
                on_release=lambda instance, x=dialogo_advertencia: self.cambiar_especialidad(
                    instance, x
                ),
                style="text",
            ),
            spacing="8dp",
        )
        dialogo_advertencia.add_widget(botones)
        dialogo_advertencia.open()

    def cambiar_especialidad(self, instance, dialogo, *args):
        self.add_widget(Login())
        pantalla_login = self.get_screen("Login")
        pantalla_login.ids["nombre_usuario"].text = self.texto_nombre
        if self.datos_usuario_horario: 
            self.guardar_datos_horario()
            self.datos_usuario_horario = None
        self.texto_especialidad = ""
        self.texto_mencion = ""
        self.icono_especialidad = "arrow-right-bold"
        self.icono_mencion = "arrow-right-bold"
        dialogo.dismiss()
        self.current = "Login"

    # Configuración-Velocidad de carga
    @auto_save_usuario
    def velocidad_carga(self, x):
        self.tiempo_espera = x
        pantalla_configuracion = self.get_screen("Configuracion")
        if x == 0.10:
            self.texto_tiempo_espera = "Rápida"
            pantalla_configuracion.tiempo_espera = "Rápida"
        else:
            self.texto_tiempo_espera = "Optimizada"
            pantalla_configuracion.tiempo_espera = "Optimizada"
        self.menu_velocidad_carga.dismiss()

    # Pantalla Horario
    def cargar_datos_horario(self, *args):
        """Carga datos locales y decide si buscar actualización automática."""
        
        # 1. Intentar cargar Base de Datos (Horarios)
        try:
            ruta_db = join(RUTA_ARCHIVOS, "base_datos_horario", "base_datos.json")
            Logger.info(f"Cargando DB horario: {ruta_db}")
            with open(ruta_db, "r", encoding="utf-8") as archivo:
                self.base_datos_horario = json.load(archivo)
        except (FileNotFoundError, json.JSONDecodeError):
            self.base_datos_horario = None
            Logger.warning("No hay base de datos local válida.")

        # 2. Intentar cargar Metadatos (Versión, Lapso, Fecha)
        try:
            ruta_ver = join(RUTA_ARCHIVOS, "base_datos_horario", "version_local.json")
            with open(ruta_ver, "r", encoding="utf-8") as archivo:
                data = json.load(archivo)
                self.version_local_horario = data.get("version", 0)
                self.pantalla_horario.texto_lapso_academico = data.get("lapso", "---")
                self.pantalla_horario.texto_fecha_actualizacion = data.get("fecha_actualizacion", "---")
        except Exception:
            self.version_local_horario = 0
            self.pantalla_horario.texto_lapso_academico = "---"
            self.pantalla_horario.texto_fecha_actualizacion = "---"

        # 3. Lógica de Automatización
        if self.base_datos_horario is None:
            # CASO PRIMERA VEZ: Bloquear UI y tratar de descargar
            Logger.info("Instalación limpia. Iniciando descarga automática...")
            Clock.schedule_once(lambda dt: self.validar_estado_ui_horario(), 0.1)
            # Damos un pequeño delay para que la UI cargue antes de lanzar la petición
            Clock.schedule_once(lambda dt: self.iniciar_actualizacion_horario(), 1.5)
        else:
            # CASO NORMAL: Solo validar botones
            Clock.schedule_once(lambda dt: self.validar_estado_ui_horario(), 0.1)

    def cargar_datos_horario_usuario(self, *args):
        try:
            Logger.info("Cargando datos de usuario de horario")
            with open(join(RUTA_ARCHIVOS, "datos_usuario", f"datos_usuario_{self.texto_especialidad.replace(".","")}{self.texto_mencion}.json"), "r",
            encoding="utf-8") as archivo:
                self.datos_usuario_horario = json.load(archivo)
                Logger.debug("Archivo cargado correctamente")
        except FileNotFoundError as e:
            self.datos_usuario_horario = {"Materias": []}
            Logger.warning("No hay archivo de base de datos horario")

        async def carga_asincrona(self):
            contenedor = self.pantalla_horario.ids["contenedor_horario"]
            for codigo in self.datos_usuario_horario["Materias"]:
                await ak.sleep(0)
                secciones_disponibles = self.datos_usuario_horario[codigo]
                materia = self.buscar_por_codigo(codigo)
                panel = ExpansionPanelItem(materia)
                for seccion in secciones_disponibles:
                    dias = self.formato_a_dias(seccion["FORMATO"])
                    aulas = self.simplificar_aulas(seccion["AULA"])
                    widget_seccion = Seccion(materia, seccion["SEC"], seccion["PROFESOR"], dias, seccion["ACTIVA"], aulas)
                    panel.ids["content"].add_widget(widget_seccion)

                self.datos_usuario_horario[codigo] = secciones_disponibles

                contenedor.add_widget(panel)

        if self.datos_usuario_horario["Materias"]:
            ak.start(carga_asincrona(self))

    def formato_a_dias(self, formato):
        lista_bloques = formato.split(",")
        dias = []
        for bloque in lista_bloques:
            dia = bloque[0]
            if dia not in dias:
                dias.append(dia)

        transformador = {"1": "Lun", "2": "Mar", "3": "Mie", "4": "Jue",
        "5": "Vie", "6": "Sáb"}
        dias_str = [transformador[dia] for dia in dias]

        return "/".join(dias_str)

    def simplificar_aulas(self, aulas):
        lista_aulas = aulas.split(",")
        valor_anterior = ""
        aulas_simplificadas = []
        for aula in lista_aulas:
            if aula != valor_anterior:
                aulas_simplificadas.append(aula)
            valor_anterior = aula
        return "/".join(aulas_simplificadas)

    def validar_estado_ui_horario(self):
        """Bloquea o desbloquea los botones según si hay datos."""
        if not self.pantalla_horario:
            return

        tiene_datos = self.base_datos_horario is not None and len(self.base_datos_horario) > 0
        
        # IDs definidos en main.kv
        ids = self.pantalla_horario.ids
        botones = [ids.btn_inscribir, ids.btn_todas, ids.btn_generar]

        for btn in botones:
            btn.disabled = not tiene_datos
            btn.opacity = 1 if tiene_datos else 0.5

    def iniciar_actualizacion_horario(self, *args):
        """Paso 1: Consultar archivo pequeño de versión."""
        Logger.info("Buscando actualizaciones...")
        MDSnackbar(
            MDSnackbarText(text='Conectando con el servidor...', halign="center"),
            duration=5, pos_hint={"center_x": 0.5}, y=dp(5), size_hint_x=0.8).open()

        UrlRequest(
            URL_VERSION_HORARIO,
            on_success=self._verificar_version,
            on_error=self._error_actualizacion,
            on_failure=self._error_actualizacion,
            ca_file=certifi.where()
        )

    def _verificar_version(self, req, result):
        """Paso 2: Comparar versiones."""
        if isinstance(result, str):
            result = json.loads(result)
        try:
            version_remota = result.get("version", 0)
            
            if version_remota > self.version_local_horario:
                Logger.info(f"Actualización detectada: v{version_remota}")
                MDSnackbar(
                    MDSnackbarText(text='Descargando nuevos horarios...', halign="center"),
                    duration=5, pos_hint={"center_x": 0.5}, y=dp(5), size_hint_x=0.8).open()
                # Pasamos 'result' completo porque contiene los metadatos (lapso, fecha)
                self._descargar_base_datos(result)
            else:
                # Si es instalación limpia pero la versión remota es 0 o error, forzamos descarga si no hay datos
                if self.base_datos_horario is None:
                     self._descargar_base_datos(result)
                else:
                    MDSnackbar(
                        MDSnackbarText(text="Los datos ya están actualizados", halign="left"),
                        MDSnackbarSupportingText(
                            text=result.get("mensaje", "---")
                        ),duration=5, pos_hint={"center_x": 0.5}, y=dp(5), size_hint_x=0.8).open()
        except Exception as e:
            self._error_actualizacion(req, error=e)

    def _descargar_base_datos(self, meta_data_version):
        """Paso 3: Descargar el archivo JSON grande."""
        UrlRequest(
            URL_BASE_DATOS_HORARIO,
            on_success=lambda req, res: self._guardar_nueva_base(req, res, meta_data_version),
            on_error=self._error_actualizacion,
            on_failure=self._error_actualizacion,
            ca_file=certifi.where()
        )

    def _guardar_nueva_base(self, req, result, meta_data_version):
        """Paso 4: Guardar en disco y actualizar memoria."""
        if isinstance(result, str):
            result = json.loads(result)
        try:
            carp_destino = join(RUTA_ARCHIVOS, "base_datos_horario")
            os.makedirs(carp_destino, exist_ok=True)

            # A. Guardar DB Grande
            with open(os.path.join(carp_destino, "base_datos.json"), "w", encoding="utf-8") as f:
                json.dump(result, f, indent = 4)

            # B. Guardar Metadata
            with open(os.path.join(carp_destino, "version_local.json"), "w", encoding="utf-8") as f:
                json.dump(meta_data_version, f, indent = 4)

            # C. Actualizar Memoria y UI
            self.base_datos_horario = result
            self.version_local_horario = meta_data_version.get("version", 0)
            self.pantalla_horario.texto_lapso_academico = meta_data_version.get("lapso", "---")
            self.pantalla_horario.texto_fecha_actualizacion = meta_data_version.get("fecha_actualizacion", "---")
            
            # Recargar y avisar
            self.actualizar_interfaz_horario()
            MDSnackbar(
                MDSnackbarText(text='¡Base de datos actualizada!', halign="center"),
                duration=5, pos_hint={"center_x": 0.5}, y=dp(5), size_hint_x=0.8).open()

        except Exception as e:
            Logger.error(f"Error escribiendo archivos: {e}")
            self._error_actualizacion(req, error="Error de escritura")

    def _error_actualizacion(self, req, error=None):
        """Manejo de errores según criticidad."""
        Logger.error(f"Fallo actualización: {error}")
        
        if self.base_datos_horario is None:
            # CRÍTICO: El usuario no puede usar el horario
            MDSnackbar(
                MDSnackbarText(text='Error de conexión', halign="left"),
                MDSnackbarSupportingText(
                    text="Se requiere internet para actualizar la información de horarios. Revisa tu conexión y toca la nube."
                ),duration=5, pos_hint={"center_x": 0.5}, y=dp(5), size_hint_x=0.8).open()
        else:
            # LEVE: El usuario tiene datos viejos, puede seguir usándolos
            MDSnackbar(
                MDSnackbarText(text='No se pude actualizar', halign="left"),
                MDSnackbarSupportingText(
                    text="Verifica tu conexión. Se mantienen los datos actuales."
                ), duration=5, pos_hint={"center_x": 0.5}, y=dp(5), size_hint_x=0.8).open()

    @auto_save_horario
    def alternar_secciones(self, checkbox, materia, nro_seccion):
        secciones = self.datos_usuario_horario[materia.codigo]
        for seccion in secciones:
            if seccion["SEC"] == nro_seccion:
                seccion["ACTIVA"] = checkbox.active

    def actualizar_interfaz_horario(self, *args):
        """Renderiza la lista de materias (llamada al entrar a la pantalla)."""
        self.validar_estado_ui_horario()

        if not self.base_datos_horario:
            MDSnackbar(
                MDSnackbarText(text="¡Datos no encontrados!", halign="center"),
                MDSnackbarSupportingText(
                    text="Se requiere internet para descargar los horarios por primera vez.",
                    theme_text_color="Custom", text_color=self.LETRA_FUERTE,
                ),
                pos_hint={"center_x": 0.5}, y=dp(10), size_hint_x=0.9
            ).open()
            return

        async def carga_asincrona(self):
            contenedor = self.pantalla_horario.ids["contenedor_horario"]
            paneles_agregados = contenedor.children
            materias_agregadas = [panel.materia for panel in paneles_agregados]
            borradas = []
            borrados = []
            for i,materia in enumerate(materias_agregadas):
                if materia.codigo not in self.datos_usuario_horario["Materias"]:
                    borrados.append(paneles_agregados[i])
                    borradas.append(materia)

            for panel in borrados:
                contenedor.remove_widget(panel)
            for materia in borradas:
                if materia.codigo in self.datos_usuario_horario:
                    del self.datos_usuario_horario[materia.codigo]
                materias_agregadas.remove(materia)

            codigos_agregados = [materia.codigo for materia in materias_agregadas]

            materias_sin_datos = []
            self.datos_usuario_horario["Materias"]
            for codigo in self.datos_usuario_horario["Materias"]:
                await ak.sleep(0)
                if codigo not in codigos_agregados:
                    if codigo in self.base_datos_horario:
                        secciones_disponibles = self.base_datos_horario[codigo]
                        materia = self.buscar_por_codigo(codigo)
                        panel = ExpansionPanelItem(materia)
                        for seccion in secciones_disponibles:
                            await ak.sleep(0)
                            dias = self.formato_a_dias(seccion["FORMATO"])
                            aulas = self.simplificar_aulas(seccion["AULA"])
                            widget_seccion = Seccion(materia, seccion["SEC"], seccion["PROFESOR"], dias, True, aulas)
                            seccion["ACTIVA"] = True
                            panel.ids["content"].add_widget(widget_seccion)

                        self.datos_usuario_horario[codigo] = secciones_disponibles

                        contenedor.add_widget(panel)
                    else:
                        materias_sin_datos.append(self.buscar_por_codigo(codigo))

            if materias_sin_datos:
                materias_str = ""
                for materia in materias_sin_datos:
                    self.datos_usuario_horario["Materias"].remove(materia.codigo)
                    materias_str += f"- {materia.nombre} ({materia.codigo})\n"
                    self.guardar_datos_horario()

                dialogo_advertencia = MDDialog(
                    MDDialogIcon(icon="alert", theme_icon_color="Custom", icon_color=self.AMARILLO),
                    MDDialogHeadlineText(text="Datos No Encontrados"),
                    MDDialogSupportingText(text=f"No se encontraron los datos de la(s) siguiente(s) materia(s) en las matrices de horario:\n{materias_str}\nEsto puede deberse a que:\n- No se publicaron secciones para la(s) materia(s).\n- Se publicaron secciones pero hay algún error en las matrices de horario.\n- Ocurrió un error al procesar los datos de las matrices de horario.", halign="left",),
                    size_hint_x=0.9,
                    size_hint_y=None,
                    radius=dp(10),
                    ripple_duration_in_fast=0,
                    ripple_duration_in_slow=0,
                    theme_focus_color="Custom",
                    focus_color=[1, 1, 1, 0],
                    padding="0dp",
                    state_press=0,
                )
                botones = MDDialogButtonContainer(
                    Widget(),
                    MDButton(
                        MDButtonText(
                            text="[b]Cerrar[/b]",
                            theme_text_color="Custom",
                            text_color=self.CYAN,
                            markup=True,
                        ),
                        on_release=lambda instance, dialogo=dialogo_advertencia: self.cerrar_dialogo(
                            dialogo
                        ),
                        style="text",
                    ),
                )
                dialogo_advertencia.add_widget(botones)
                dialogo_advertencia.open()


        ak.start(carga_asincrona(self))

    def dialogo_agregar_materias_horario(self, disponible):
        lista_materias = self.get_materias()
        recycle_view_materias = RVHorario(lista_materias, self.datos_usuario_horario["Materias"], disponible)
        menu_seleccion = MDDialog(
            MDDialogIcon(
                icon="information",
                theme_icon_color="Custom",
                icon_color=self.AZUL_CLARO,
            ),
            MDDialogHeadlineText(text="Agregar Materias"),
            MDDialogContentContainer(recycle_view_materias, orientation="vertical"),
            size_hint_x=0.9,
            radius=dp(10),
            ripple_scale=0,
            theme_focus_color="Custom",
            padding="0dp",
            hide_duration=0.5,
            state_press=0,
        )
        menu_seleccion.bind(
            on_dismiss=lambda instance: self.finalizar_seleccion()
        )
        boton_aceptar = MDDialogButtonContainer(
            Widget(),
            MDButton(
                MDButtonText(
                    text="[b]Aceptar[/b]",
                    theme_text_color="Custom",
                    text_color=self.CYAN,
                    markup=True,
                ),
                on_release=lambda instance, dialogo=menu_seleccion: self.cerrar_dialogo(
                    dialogo
                ),
                style="text",
            ),
        )
        menu_seleccion.add_widget(boton_aceptar)
        menu_seleccion.open()

    @auto_save_horario
    def finalizar_seleccion(self):
        Clock.schedule_once(self.actualizar_interfaz_horario, 1)
        self.pantalla_horario.ids["scroll_horario"].scroll_y = 1

    def editar_formato_materia(self, materia, nro_seccion):
        def editar(campo, focus, seccion):
            if not focus:
                seccion["FORMATO"] = campo.text
                self.guardar_datos_horario()

        secciones = self.datos_usuario_horario[materia.codigo]
        seccion = {}
        for sec in secciones:
            if sec["SEC"] == nro_seccion:
                seccion = sec

        campo_texto = MDTextField(text=seccion["FORMATO"], pos_hint={"center_x": 0.5}, max_height=dp(40),
                write_tab=False, multiline=False, use_bubble=False, halign="center", input_type="number")
        dialogo_advertencia = MDDialog(
                MDDialogSupportingText(
                    text=f"Editar sección {nro_seccion} de {materia.nombre}", theme_font_size="Custom", font_size="20sp"
                ),
                MDDialogContentContainer(campo_texto, orientation="vertical"),
                radius=dp(15),
                ripple_duration_in_fast=0,
                ripple_duration_in_slow=0,
                theme_focus_color="Custom",
                focus_color=[1, 1, 1, 0],
                padding="0dp",
                state_press=0,
            )
        botones = MDDialogButtonContainer(Widget(),
                MDButton(
                    MDButtonText(
                        text="[b]Aceptar[/b]",
                        theme_text_color="Custom",
                        text_color=self.CYAN,
                        markup=True,
                    ),
                    on_release=lambda instance, dialogo=dialogo_advertencia: self.cerrar_dialogo(
                        dialogo
                    ),
                    style="text",
                ),
            )

        dialogo_advertencia.add_widget(botones)
        dialogo_advertencia.open()
        campo_texto.bind(focus=lambda instance, focus, seccion = seccion: editar(instance, focus, seccion))

    def accion_boton_crear_horario(self):
        if not self.has_screen("GenerarHorario"):
            self.add_widget(GenerarHorario())
            self.pantalla_generar_horario = self.get_screen("GenerarHorario")

        self.current = "GenerarHorario"
        self.cambiar_colores = True
        Clock.schedule_once(self.crear_bloques_horario, 1)
        if not self.activado_bloques_horario:
            for box in self.bloques_horario_materias:
                padre = box.parent
                padre.remove_widget(box)
            self.bloques_horario_materias.clear()
            self.crear_horarios(self.numero_horario)

    def crear_bloques_horario(self, *args):
        if self.activado_bloques_horario:
            self.bloques_horario = []
            self.activado_bloques_horario = False
            dias = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado"]
            dia = 0
            hora = 6
            for i in range(66):
                if i % 11 == 0:
                    texto = str(dias[int(i / 11)])
                    Id = str(dias[int(i / 11)])
                    hora = 6
                    dia += 1
                    box_layout = MDBoxLayout(
                        MDLabel(id=f"{Id}l", text=texto, halign="center"),
                        id=f"{Id}b",
                        orientation="vertical",
                        size_hint_x=None,
                        size_hint_y=1,
                        width=self.pantalla_generar_horario.ids[
                            "GridLayoutHorario"
                        ].width
                        / 7,
                        md_bg_color=self.color_fondo_claro,
                    )
                else:
                    texto = ""
                    hora += 1
                    Id = f"{dia}{hora}"
                    box_layout = MDBoxLayout(
                        id=f"{Id}b",
                        orientation="horizontal",
                        size_hint_x=None,
                        size_hint_y=1,
                        width=self.pantalla_generar_horario.ids[
                            "GridLayoutHorario"
                        ].width
                        / 7,
                        md_bg_color=self.color_fondo_claro,
                    )

                self.bloques_horario.append(box_layout)
                self.pantalla_generar_horario.ids["GridLayoutHorario"].add_widget(
                    box_layout
                )
            self.numero_horario = 0
            self.crear_horarios(0)

    def crear_horarios(self, numero_horario):
        lista_colores = ["lightsalmon","cornflowerblue","springgreen","yellow","mediumorchid",
            "tomato","orange","deeppink","gray","cyan","lime"]
        lista_maestra = []
        dia = 0
        hora = 6
        lista_posibles_bloques = []
        lista_bloques_omitidos = [117,118,119,217,218,219,317,318,319,417,418,
            419,517,518,519,617,618,619]
        lista_para_opcion = []
        for i in range(66):
            if i % 11 == 0:
                hora = 6
                dia += 1
            else:
                hora += 1
                lista_posibles_bloques.append(int(f"{dia}{hora}"))

        error_formato_horario = False
        error_hora = False
        error_formato_simbolo = False
        codigos = []
        formatos = []
        secciones = []
        profesores = []
        materias = self.datos_usuario_horario["Materias"]
        for materia in materias:
            secs = self.datos_usuario_horario[materia]
            formato = []
            seccion = []
            profesor = []
            for sec in secs:
                if sec["ACTIVA"]:
                    formato.append(sec["FORMATO"])
                    seccion.append(sec["SEC"])
                    profesor.append(sec["PROFESOR"].replace(",", ""))

            if formato:
                codigos.append(materia)
                formatos.append("-".join(formato))
                secciones.append(",".join(seccion))
                profesores.append(",".join(profesor))

        for i,formato in enumerate(formatos):
            if formato != "":
                lista_opciones = [str(x) for x in formato.split("-")]
                lista_bloques = []
                for opcion in lista_opciones:
                    try:
                        lista_para_opcion = [int(x) for x in opcion.split(",")]
                    except ValueError as e:
                        error_formato_simbolo = True
                    bloques_excluidos = []
                    for bloque in lista_para_opcion:
                        if bloque not in lista_posibles_bloques:
                            error_formato_horario = True
                            if bloque in lista_bloques_omitidos:
                                bloques_excluidos.append(bloque)
                                error_formato_horario = False
                    if bloques_excluidos:
                        for bloque in bloques_excluidos:
                            lista_para_opcion.remove(bloque)

                    lista_bloques.append(lista_para_opcion)
                lista_maestra.append(lista_bloques)

        lista_secciones = []
        lista_profesores = []
        lista_opciones = []

        error_formato = False
        for i, seccion in enumerate(secciones):
            if seccion == "":
                lista_opciones = []
                for x in range(len(lista_maestra[i])):
                    lista_opciones.append("")
            else:
                lista_opciones = [str(x) for x in seccion.split(",")]

            if len(lista_opciones) != len(lista_maestra[i]):
                error_formato = True

            lista_secciones.append(lista_opciones)

            lista_opciones = []
            profesor = profesores[i]
            if profesor == "":
                for x in range(len(lista_maestra[i])):
                    lista_opciones.append("")
            else:
                lista_opciones = [str(x) for x in profesor.split(",")]

            if len(lista_opciones) != len(lista_maestra[i]):
                error_formato = True
            lista_profesores.append(lista_opciones)

        if (error_formato_horario or error_formato_simbolo or error_formato):
            self.current = "Horario"

        if error_formato_horario:
            MDSnackbar(
                MDSnackbarText(text='Error en "Formato Horario"', halign="left"),
                MDSnackbarSupportingText(
                    text="Bloque de horario (DiaHora) incorrecto. Se deben ingresar los bloques (DiaHora) separados por coma."
                ),
                duration=8,
                pos_hint={"center_x": 0.5},
                y=dp(5),
                size_hint_x=0.8,
            ).open()
        elif error_formato_simbolo:
            MDSnackbar(
                MDSnackbarText(text='Error en "Formato Horario"', halign="left"),
                MDSnackbarSupportingText(
                    text="Valor incorrecto. Solo se pueden ingresar números, comas y guiones"
                ),
                duration=8,
                pos_hint={"center_x": 0.5},
                y=dp(5),
                size_hint_x=0.8,
            ).open()
        elif error_formato:
            MDSnackbar(
                MDSnackbarText(
                    text='Error en "Seccion" y/o "Profesor"', halign="left"
                ),
                MDSnackbarSupportingText(
                    text="Se debe ingresar una sección y/o profesor separado por coma para cada opción de horario de la materia"
                ),
                duration=8,
                pos_hint={"center_x": 0.5},
                y=dp(5),
                size_hint_x=0.8,
            ).open()
        else:
            combinaciones_formato = list(product(*lista_maestra))
            combinaciones_secciones = list(product(*lista_secciones))
            combinaciones_profesores = list(product(*lista_profesores))

            self.max_horarios = len(combinaciones_formato)
            self.pantalla_generar_horario.max_horarios = self.max_horarios
            choques_por_horario = []

            for horario in combinaciones_formato:
                repetidos = set()
                contador_choques = 0
                for materia in horario:
                    for bloque in materia:
                        if bloque in repetidos:
                            contador_choques += 1
                        else:
                            repetidos.add(bloque)
                choques_por_horario.append(contador_choques)

            combinaciones_formato_sin_ordenar = combinaciones_formato.copy()
            combinaciones_secciones_sin_ordenar = combinaciones_secciones.copy()
            combinaciones_profesores_sin_ordenar = combinaciones_profesores.copy()
            choques_sin_ordenar = choques_por_horario.copy()
            choques_por_horario.sort()
            
            for i,choque in enumerate(choques_por_horario):
                ubicacion_anterior = choques_sin_ordenar.index(choque)
                choques_sin_ordenar[ubicacion_anterior] = ""
                combinaciones_formato[i] = combinaciones_formato_sin_ordenar[
                    ubicacion_anterior
                ]
                combinaciones_secciones[i] = combinaciones_secciones_sin_ordenar[
                    ubicacion_anterior
                ]
                combinaciones_profesores[i] = combinaciones_profesores_sin_ordenar[
                    ubicacion_anterior
                ]

            try:
                horario = combinaciones_formato[numero_horario]
            except IndexError as e:
                numero_horario = 0
                self.numero_horario = 0

            horario = combinaciones_formato[numero_horario]
            secciones = combinaciones_secciones[numero_horario]
            profesores = combinaciones_profesores[numero_horario]

            if self.cambiar_colores:
                self.color = random.sample(lista_colores, k=11)
                self.cambiar_colores = False

            repetidos = set()
            contador_choques = 0

            for i,materia in enumerate(horario):
                nombre = self.buscar_por_codigo(codigos[i]).nombre
                lista_de_bloques = materia
                bloques_consecutivos = 0
                pasos_restantes = 0
                for bloque in materia:
                    # Verificar bloques consecutivos
                    if pasos_restantes == 0:
                        posicion_bloque_global = lista_posibles_bloques.index(bloque)
                        posicion_bloque_local = lista_de_bloques.index(bloque)
                        if (posicion_bloque_local + 1) < len(
                            lista_de_bloques
                        ) and posicion_bloque_global + 1 < len(lista_posibles_bloques):
                            if (
                                lista_de_bloques[posicion_bloque_local + 1]
                                == lista_posibles_bloques[posicion_bloque_global + 1]
                            ):
                                bloques_consecutivos = 2
                                if (posicion_bloque_local + 2) < len(
                                    lista_de_bloques
                                ) and (posicion_bloque_global + 2) < len(
                                    lista_posibles_bloques
                                ):
                                    if (
                                        lista_de_bloques[posicion_bloque_local + 2]
                                        == lista_posibles_bloques[
                                            posicion_bloque_global + 2
                                        ]
                                    ):
                                        bloques_consecutivos = 3
                                        if (posicion_bloque_local + 3) < len(
                                            lista_de_bloques
                                        ) and (posicion_bloque_global + 3) < len(
                                            lista_posibles_bloques
                                        ):
                                            if (
                                                lista_de_bloques[
                                                    posicion_bloque_local + 3
                                                ]
                                                == lista_posibles_bloques[
                                                    posicion_bloque_global + 3
                                                ]
                                            ):
                                                bloques_consecutivos = 4
                                                if (posicion_bloque_local + 4) < len(
                                                    lista_de_bloques
                                                ) and (
                                                    posicion_bloque_global + 4
                                                ) < len(
                                                    lista_posibles_bloques
                                                ):
                                                    if (
                                                        lista_de_bloques[
                                                            posicion_bloque_local + 4
                                                        ]
                                                        == lista_posibles_bloques[
                                                            posicion_bloque_global + 4
                                                        ]
                                                    ):
                                                        bloques_consecutivos = 5
                        pasos_restantes = bloques_consecutivos

                    if bloque in repetidos:
                        contador_choques += 1
                    else:
                        repetidos.add(bloque)

                    for boxlayout in self.bloques_horario:
                        if boxlayout.id == f"{bloque}b":
                            if secciones[i] == "":
                                texto_seccion = ""
                            else:
                                texto_seccion = f"Secc. {secciones[i]}"

                            if bloques_consecutivos == 0:
                                boxlayout_materia = MDBoxLayout(
                                    MDLabel(
                                        markup=True,
                                        text=f"[b]{nombre}[/b] {texto_seccion}\n{profesores[i]}",
                                        theme_font_size="Custom",
                                        font_size="9sp",
                                        halign="center",
                                        theme_line_height="Custom",
                                        line_height=0.85,
                                        theme_text_color="Custom",
                                        text_color="black",
                                    ),
                                    md_bg_color=self.color[i],
                                )
                            elif bloques_consecutivos == 2:
                                if pasos_restantes == 2:
                                    boxlayout_materia = MDBoxLayout(
                                        MDLabel(
                                            markup=True,
                                            text=f"[b]{nombre}[/b]",
                                            theme_font_size="Custom",
                                            font_size="9sp",
                                            halign="center",
                                            theme_line_height="Custom",
                                            line_height=0.85,
                                            theme_text_color="Custom",
                                            text_color="black",
                                        ),
                                        md_bg_color=self.color[i],
                                    )
                                    pasos_restantes -= 1
                                elif pasos_restantes == 1:
                                    boxlayout_materia = MDBoxLayout(
                                        MDLabel(
                                            markup=True,
                                            text=f"{texto_seccion}\n{profesores[i]}",
                                            theme_font_size="Custom",
                                            font_size="9sp",
                                            halign="center",
                                            theme_line_height="Custom",
                                            line_height=0.85,
                                            theme_text_color="Custom",
                                            text_color="black",
                                        ),
                                        md_bg_color=self.color[i],
                                    )
                                    pasos_restantes -= 1
                                    bloques_consecutivos = 0
                            elif bloques_consecutivos == 3:
                                if pasos_restantes == 3:
                                    boxlayout_materia = MDBoxLayout(
                                        MDLabel(
                                            markup=True,
                                            text=f"[b]{nombre}[/b]",
                                            theme_font_size="Custom",
                                            font_size="9sp",
                                            halign="center",
                                            theme_line_height="Custom",
                                            line_height=0.85,
                                            theme_text_color="Custom",
                                            text_color="black",
                                        ),
                                        md_bg_color=self.color[i],
                                    )
                                    pasos_restantes -= 1
                                elif pasos_restantes == 2:
                                    boxlayout_materia = MDBoxLayout(
                                        MDLabel(
                                            markup=True,
                                            text=f"{texto_seccion}",
                                            theme_font_size="Custom",
                                            font_size="9sp",
                                            halign="center",
                                            theme_line_height="Custom",
                                            line_height=0.85,
                                            theme_text_color="Custom",
                                            text_color="black",
                                        ),
                                        md_bg_color=self.color[i],
                                    )
                                    pasos_restantes -= 1
                                elif pasos_restantes == 1:
                                    boxlayout_materia = MDBoxLayout(
                                        MDLabel(
                                            markup=True,
                                            text=f"{profesores[i]}",
                                            theme_font_size="Custom",
                                            font_size="9sp",
                                            halign="center",
                                            theme_line_height="Custom",
                                            line_height=0.85,
                                            theme_text_color="Custom",
                                            text_color="black",
                                        ),
                                        md_bg_color=self.color[i],
                                    )
                                    pasos_restantes -= 1
                                    bloques_consecutivos = 0
                            elif bloques_consecutivos == 4:
                                if pasos_restantes == 4 or pasos_restantes == 1:
                                    boxlayout_materia = MDBoxLayout(
                                        MDLabel(
                                            markup=True,
                                            text=f"",
                                            theme_font_size="Custom",
                                            font_size="9sp",
                                            halign="center",
                                            theme_line_height="Custom",
                                            line_height=0.85,
                                            theme_text_color="Custom",
                                            text_color="black",
                                        ),
                                        md_bg_color=self.color[i],
                                    )
                                    if pasos_restantes == 1:
                                        bloques_consecutivos = 0
                                    pasos_restantes -= 1
                                elif pasos_restantes == 3:
                                    boxlayout_materia = MDBoxLayout(
                                        MDLabel(
                                            markup=True,
                                            text=f"[b]{nombre}[/b]",
                                            theme_font_size="Custom",
                                            font_size="9sp",
                                            halign="center",
                                            theme_line_height="Custom",
                                            line_height=0.85,
                                            theme_text_color="Custom",
                                            text_color="black",
                                        ),
                                        md_bg_color=self.color[i],
                                    )
                                    pasos_restantes -= 1
                                elif pasos_restantes == 2:
                                    boxlayout_materia = MDBoxLayout(
                                        MDLabel(
                                            markup=True,
                                            text=f"{texto_seccion}\n{profesores[i]}",
                                            theme_font_size="Custom",
                                            font_size="9sp",
                                            halign="center",
                                            theme_line_height="Custom",
                                            line_height=0.85,
                                            theme_text_color="Custom",
                                            text_color="black",
                                        ),
                                        md_bg_color=self.color[i],
                                    )
                                    pasos_restantes -= 1
                            elif bloques_consecutivos == 5:
                                if pasos_restantes == 5 or pasos_restantes == 1:
                                    boxlayout_materia = MDBoxLayout(
                                        MDLabel(
                                            markup=True,
                                            text=f"",
                                            theme_font_size="Custom",
                                            font_size="9sp",
                                            halign="center",
                                            theme_line_height="Custom",
                                            line_height=0.85,
                                            theme_text_color="Custom",
                                            text_color="black",
                                        ),
                                        md_bg_color=self.color[i],
                                    )
                                    if pasos_restantes == 1:
                                        bloques_consecutivos = 0
                                    pasos_restantes -= 1
                                elif pasos_restantes == 4:
                                    boxlayout_materia = MDBoxLayout(
                                        MDLabel(
                                            markup=True,
                                            text=f"[b]{nombre}[/b]",
                                            theme_font_size="Custom",
                                            font_size="9sp",
                                            halign="center",
                                            theme_line_height="Custom",
                                            line_height=0.85,
                                            theme_text_color="Custom",
                                            text_color="black",
                                        ),
                                        md_bg_color=self.color[i],
                                    )
                                    pasos_restantes -= 1
                                elif pasos_restantes == 3:
                                    boxlayout_materia = MDBoxLayout(
                                        MDLabel(
                                            markup=True,
                                            text=f"{texto_seccion}",
                                            theme_font_size="Custom",
                                            font_size="9sp",
                                            halign="center",
                                            theme_line_height="Custom",
                                            line_height=0.85,
                                            theme_text_color="Custom",
                                            text_color="black",
                                        ),
                                        md_bg_color=self.color[i],
                                    )
                                    pasos_restantes -= 1
                                elif pasos_restantes == 2:
                                    boxlayout_materia = MDBoxLayout(
                                        MDLabel(
                                            markup=True,
                                            text=f"{profesores[i]}",
                                            theme_font_size="Custom",
                                            font_size="9sp",
                                            halign="center",
                                            theme_line_height="Custom",
                                            line_height=0.85,
                                            theme_text_color="Custom",
                                            text_color="black",
                                        ),
                                        md_bg_color=self.color[i],
                                    )
                                    pasos_restantes -= 1

                            self.bloques_horario_materias.append(boxlayout_materia)
                            boxlayout.add_widget(boxlayout_materia)

            MDSnackbar(
                MDSnackbarText(
                    text=f"Horario #{numero_horario+1} - Choques: {contador_choques}",
                    halign="center",
                ),
                duration=3,
                pos_hint={"center_x": 0.92, "center_y": 0.5},
                size_hint_x=0.5,
                rotate_value_angle=90,
                theme_focus_color="Custom",
                focus_color=[1, 1, 1, 0],
                ripple_color=[1, 1, 1, 0],
                state_press=0,
            ).open()

    def siguiente_horario(self, paso):
        if self.numero_horario < self.max_horarios - paso:
            self.numero_horario += paso
            self.pantalla_generar_horario.numero_horario = self.numero_horario
            for box in self.bloques_horario_materias:
                padre = box.parent
                padre.remove_widget(box)
            self.bloques_horario_materias.clear()
            self.crear_horarios(self.numero_horario)

    def anterior_horario(self, paso):
        if self.numero_horario - paso >= 0:
            self.numero_horario -= paso
            self.pantalla_generar_horario.numero_horario = self.numero_horario
            for box in self.bloques_horario_materias:
                padre = box.parent
                padre.remove_widget(box)
            self.bloques_horario_materias.clear()
            self.crear_horarios(self.numero_horario)

    def mostrar_guia_horario(self, *args):
        if self.guia_horario:
            dialogo_informacion = MDDialog(
                MDDialogIcon(
                    icon="information",
                    theme_icon_color="Custom",
                    icon_color=self.AZUL_CLARO,
                ),
                MDDialogHeadlineText(text="[b]Guía de [i]Horario[/i][/b]"),
                MDDialogSupportingText(
                    text="[b]Selección:[/b] Agrega las materias que deseas cursar desde seleccionar materias. Puedes elegir entre las disponibles según tu pensum o buscar en la lista completa. Luego puedes seleccionar las secciones disponibles de tu interés.\n\n[b]Generación:[/b] La app calculará todas las combinaciones de secciones posibles, ordenándolas para mostrarte primero las opciones sin choques de horas.\n\n[b]Exportar:[/b] Una vez generado, navega entre las opciones y guarda tu horario ideal como [b]Imagen[/b] o [b]PDF[/b].\n\n*Recuerda actualizar la base de datos tocando el icono de la nube.",
                    markup=True,
                    halign="left",
                ),
                size_hint_x=0.9,
                size_hint_y=None,
                radius=dp(10),
                ripple_duration_in_fast=0,
                ripple_duration_in_slow=0,
                theme_focus_color="Custom",
                focus_color=[1, 1, 1, 0],
                padding="0dp",
                state_press=0,
                auto_dismiss=False,
            )
            boton = MDDialogButtonContainer(
                Widget(),
                MDButton(
                    MDButtonText(
                        text="[b]Cerrar[/b]",
                        theme_text_color="Custom",
                        text_color=self.CYAN,
                        markup=True,
                    ),
                    on_release=lambda instance, x=dialogo_informacion: self.cerrar_dialogo(x),
                    style="text",
                ),
            )
            dialogo_informacion.add_widget(boton)
            dialogo_informacion.open()
            self.guia_horario = False

    def advertencia_borrar_datos_horario(self):
        dialogo_advertencia = MDDialog(
            MDDialogIcon(
                icon="alert", theme_icon_color="Custom", icon_color=self.AMARILLO
            ),
            MDDialogHeadlineText(text="¿Confirmar?"),
            MDDialogSupportingText(
                text="¡Se quitaran todas las materias de la lista!",
                halign="left",
            ),
            size_hint_x=0.9,
            size_hint_y=None,
            radius=[dp(10), dp(10), dp(10), dp(10)],
            ripple_duration_in_fast=0,
            ripple_duration_in_slow=0,
            theme_focus_color="Custom",
            focus_color=[1, 1, 1, 0],
            padding="0dp",
            state_press=0,
        )
        botones = MDDialogButtonContainer(
            Widget(),
            MDButton(
                MDButtonText(
                    text="[b]Cancelar[/b]",
                    theme_text_color="Custom",
                    text_color=self.CYAN,
                    markup=True,
                ),
                on_release=lambda instance, dialogo=dialogo_advertencia: self.cerrar_dialogo(
                    dialogo
                ),
                style="text",
            ),
            MDButton(
                MDButtonText(
                    text="Borrar", theme_text_color="Custom", text_color=self.CYAN
                ),
                on_release=lambda instance, dialogo=dialogo_advertencia: self.borrar_datos_horario(
                    dialogo
                ),
                style="text",
            ),
            spacing="8dp",
        )
        dialogo_advertencia.add_widget(botones)
        dialogo_advertencia.open()

    @auto_save_horario
    def borrar_datos_horario(self, dialogo):
        self.datos_usuario_horario.clear()
        self.datos_usuario_horario["Materias"] = []
        self.pantalla_horario.ids["contenedor_horario"].clear_widgets()
        dialogo.dismiss()

    def guardar_datos_horario(self):
        try:
            Logger.info("Guardando datos de horario")
            with open(join(RUTA_DATOS, f"datos_usuario_{self.texto_especialidad.replace(".","")}{self.texto_mencion}.json"), "w",
            encoding="utf-8") as archivo:
                json.dump(self.datos_usuario_horario, archivo, indent = 4)
                Logger.debug("Archivo guardado correctamente")
        except IOError as e:
            Logger.error(f"Error al guardar datos de usuario de horario {e}")

    def guardar_imagen_horario(self, *args):
        try:
            grid_layout = self.pantalla_generar_horario.ids["GridLayoutHorario"]
            fecha = datetime.datetime.now()
            fecha_str = fecha.strftime("%d-%m-%Y %H-%M-%S")
            archivo = join(RUTA_ARCHIVOS, "Horarios", f"Horario {self.numero_horario+1} {fecha_str}.png")
            destino = os.path.dirname(archivo)
            os.makedirs(destino, exist_ok=True)
            grid_layout.export_to_png(archivo)

            if platform == "android":
                app = MDApp.get_running_app()
                app.ss.copy_to_shared(archivo)
                os.remove(archivo)

            MDSnackbar(
                MDSnackbarText(text=f"¡Imagen guardada en /Pictures!", halign="center"),
                duration=3,
                pos_hint={"center_x": 0.92, "center_y": 0.5},
                size_hint_x=0.65,
                rotate_value_angle=90,
                theme_focus_color="Custom",
                focus_color=[1, 1, 1, 0],
                ripple_color=[1, 1, 1, 0],
                state_press=0,
            ).open()
        except Exception as e:
            Logger.error(f"Error al guardar imagen {e}")
            MDSnackbar(
                MDSnackbarText(text=f"¡Error al guardar Imagen!", halign="center"),
                duration=3,
                pos_hint={"center_x": 0.92, "center_y": 0.5},
                size_hint_x=0.65,
                rotate_value_angle=90,
                theme_focus_color="Custom",
                focus_color=[1, 1, 1, 0],
                ripple_color=[1, 1, 1, 0],
                state_press=0,
            ).open()

    def guardar_pdf_horario(self, *args):
        try:
            grid_layout = self.pantalla_generar_horario.ids["GridLayoutHorario"]
            fecha = datetime.datetime.now()
            fecha_str = fecha.strftime("%d-%m-%Y %H-%M-%S")
            archivo = join(RUTA_ARCHIVOS, "Horarios", f"Horario {self.numero_horario+1} {fecha_str}.png")
            direccion_pdf = join(RUTA_ARCHIVOS, "Horarios", f"Horario {self.numero_horario+1} {fecha_str}.pdf")
            nombre_pdf = f"Horario {self.numero_horario+1} {fecha_str}.pdf"
            destino = os.path.dirname(archivo)
            os.makedirs(destino, exist_ok=True)
            grid_layout.export_to_png(archivo)
            # Crear PDF
            MARGEN = 10
            pdf = FPDF(orientation="L", unit="mm", format="Letter")
            pdf.add_page()
            ancho_util = pdf.w - (MARGEN * 2)
            with Imagepillow.open(archivo) as imagen:
                img_w, img_h = imagen.size
            ratio = img_h / img_w
            altura_imagen_escalada = ancho_util * ratio
            posicion_y = (pdf.h - altura_imagen_escalada) / 2
            pdf.image(archivo, x=MARGEN, y=posicion_y, w=ancho_util)
            pdf.output(direccion_pdf)

            if platform == "android":
                app = MDApp.get_running_app()
                app.ss.copy_to_shared(
                    direccion_pdf, filepath=f"Horarios PDF/{nombre_pdf}"
                )
                os.remove(direccion_pdf)

            MDSnackbar(
                MDSnackbarText(text=f"¡PDF guardado en Documents!", halign="center"),
                duration=3,
                pos_hint={"center_x": 0.92, "center_y": 0.5},
                size_hint_x=0.65,
                rotate_value_angle=90,
                theme_focus_color="Custom",
                focus_color=[1, 1, 1, 0],
                ripple_color=[1, 1, 1, 0],
                state_press=0,
            ).open()

        except Exception as e:
            Logger.error(f"Error al guardar PDF, {e}")
            MDSnackbar(
                MDSnackbarText(text=f"¡Error al guardar el PDF!", halign="center"),
                duration=3,
                pos_hint={"center_x": 0.92, "center_y": 0.5},
                size_hint_x=0.65,
                rotate_value_angle=90,
                theme_focus_color="Custom",
                focus_color=[1, 1, 1, 0],
                ripple_color=[1, 1, 1, 0],
                state_press=0,
            ).open()

    def tap_expansion_chevron(self, panel: FMDExpansionPanel, chevron: TrailingPressedIconButton):
        if self.panel_activado:
            self.panel_activado = False
            Animation(
                padding=[0, dp(12), 0, dp(12)]
                if not panel.is_open
                else [0, 0, 0, 0],
                d=0.2,
            ).start(panel)
            panel.open() if not panel.is_open else panel.close()
            panel.set_chevron_down(chevron) if not panel.is_open else panel.set_chevron_up(chevron)
            Clock.schedule_once(lambda dt: self.activar_panel(), 0.5)

    def activar_panel(self):
        self.panel_activado = True

class MainApp(MDApp):
    widget_principal = None
    global VERSION
    version = VERSION
    size_status = ObjectProperty(0)
    size_nav = ObjectProperty(0)
    copia_cargada = False

    def on_start(self):
        if platform == "android":
            self.dont_gc = AndroidPermissions()
            self.ss = SharedStorage()

        Logger.info("Iniciando aplicación, cargando datos de usuario")
        self.widget_principal.cargar_datos_usuario()

        Logger.info("Cargando tema de app")
        self.theme_cls.theme_style = self.widget_principal.tema_ingles
        Logger.info("Tema de app cargado")

        if self.widget_principal.requiere_login:
            Logger.info("Redirigiendo a pantalla de login")
            self.widget_principal.add_widget(Login())
            self.widget_principal.current = "Login"
            self.widget_principal.transition = SlideTransition(direction="left")

        if platform == "android" and api_version >= 35:
            self.size_status = get_height_of_bar("status")
            self.size_nav = get_height_of_bar("navigation")

    def build(self):
        self.widget_principal = Widget_Principal()
        self.theme_cls.theme_style_switch_animation = True
        self.theme_cls.primary_palette = "Blue"

        if platform == "android":
            # Android Shared Storage
            self.chooser = Chooser(self.chooser_callback)
            temp = SharedStorage().get_cache_dir()
            if temp and exists(temp):
                shutil.rmtree(temp)
            # Kivy ads
            self.admob = AdmobManager(callback=self.ad_callback)
            self.admob.load_interstitial(INTERSTITIAL)
        return self.widget_principal

    def mostrar_anuncio(self, *args):
        self.admob.show_rewarded()

    def ad_callback(self, event, *args):
        if event == "reward_earned":
            self.recompensa_obtenida()
            self.admob.load_rewarded(REWARDED)
        elif event == "ad_failed":
            Logger.error("Error al cargar anuncio")

    @mainthread
    def recompensa_obtenida(self):
        MDSnackbar(
            MDSnackbarText(
                text="¡Gracias por el apoyo!",
                markup=True,
                theme_text_color="Custom",
                text_color=self.widget_principal.LETRA_FUERTE,
            ),
            duration=5,
            pos_hint={"center_x": 0.5},
            y=dp(5),
            size_hint_x=0.95,
            theme_bg_color="Custom",
            background_color=self.widget_principal.color_fondo_mas_claro,
        ).open()

    def cambiar_tema(self):
        self.theme_cls.theme_style = ("Dark" if self.theme_cls.theme_style == "Light" else "Light")
        self.widget_principal.tema_ingles = self.theme_cls.theme_style

    def añadir_pantalla(self, pantalla):
        if pantalla == "Descargo De Responsabilidad":
            self.widget_principal.add_widget(DescargoResponsabilidad())
        elif pantalla == "Colaboradores":
            self.widget_principal.add_widget(Colaboradores())
        elif pantalla == "Licencias":
            self.widget_principal.add_widget(Licencias())

    def abrir_enlace(self, enlace, *args):
        import webbrowser
        webbrowser.open(enlace)

    def dialogo_crear_copia(self, *args):
        dialogo_advertencia = MDDialog(
            MDDialogIcon(
                icon="alert",
                theme_icon_color="Custom",
                icon_color=self.widget_principal.AMARILLO,
            ),
            MDDialogHeadlineText(text="Exportar Datos"),
            MDDialogSupportingText(
                text="Crea una copia de seguridad de tus datos, podrás restaurar esta copia si pierdes tus datos por algún error, o si quieres exportar tus datos a otro dispositivo.\n\nLa copia de seguridad se guarda en: Almacenamiento Interno/Documents/Unexum/Copias de seguridad",
                halign="left",
            ),
            size_hint_x=0.9,
            size_hint_y=None,
            radius=[dp(10), dp(10), dp(10), dp(10)],
            ripple_duration_in_fast=0,
            ripple_duration_in_slow=0,
            theme_focus_color="Custom",
            focus_color=[1, 1, 1, 0],
            padding="0dp",
            state_press=0,
        )
        botones = MDDialogButtonContainer(
            Widget(),
            MDButton(
                MDButtonText(
                    text="[b]Cancelar[/b]",
                    theme_text_color="Custom",
                    text_color=self.widget_principal.CYAN,
                    markup=True,
                ),
                on_release=lambda instance, dialogo=dialogo_advertencia: self.widget_principal.cerrar_dialogo(
                    dialogo
                ),
                style="text",
            ),
            MDButton(
                MDButtonText(
                    text="Crear Copia",
                    theme_text_color="Custom",
                    text_color=self.widget_principal.CYAN,
                ),
                on_release=lambda instance, dialogo=dialogo_advertencia: self.crear_copia(
                    dialogo
                ),
                style="text",
            ),
            spacing="8dp",
        )
        dialogo_advertencia.add_widget(botones)
        dialogo_advertencia.open()

    def crear_copia(self, dialogo, *args):
        dialogo.dismiss()
        #Guardamos datos por si se editó algo antes de crear la copiar
        self.widget_principal.guardar_datos(self.widget_principal.materias_cache)
        if self.widget_principal.datos_usuario_horario: 
                self.widget_principal.guardar_datos_horario()
        self.widget_principal.guardar_datos_usuario()

        carpeta_temporal = join(RUTA_ARCHIVOS, "copia_temporal")
        fecha = datetime.datetime.now()
        fecha_str = fecha.strftime("%d-%m-%Y %H-%M-%S")
        direccion_zip = join(RUTA_ARCHIVOS, "Copias de seguridad", f"Backup Unexum {fecha_str}.zip")
        nombre_zip = f"Backup Unexum {fecha_str}.zip"
        destino = os.path.dirname(direccion_zip)
        if carpeta_temporal and exists(carpeta_temporal):
            shutil.rmtree(carpeta_temporal)

        os.makedirs(destino, exist_ok=True)
        os.makedirs(carpeta_temporal, exist_ok=True)

        # Buscar Archivos:
        try:
            nombres_archivos = os.listdir(RUTA_DATOS)
            for nombre_archivo in nombres_archivos:
                if nombre_archivo.endswith(".json"):
                    ruta_completa_origen = join(RUTA_DATOS, nombre_archivo)
                    shutil.copy(ruta_completa_origen, carpeta_temporal)

            with zipfile.ZipFile(direccion_zip, "w") as zipf:
                for archivo in os.listdir(carpeta_temporal):
                    ruta_completa_archivo = os.path.join(carpeta_temporal, archivo)
                    zipf.write(ruta_completa_archivo, arcname=archivo)

            shutil.rmtree(carpeta_temporal)

            if platform == "android":
                app = MDApp.get_running_app()
                app.ss.copy_to_shared(
                    direccion_zip, filepath=join("Copias de seguridad",f"{nombre_zip}")
                )
                os.remove(direccion_zip)

            MDSnackbar(
                MDSnackbarText(text="Copia de seguridad creada", halign="center"),
                duration=8,
                pos_hint={"center_x": 0.5},
                y=dp(5),
                size_hint_x=0.7,
            ).open()

        except Exception as e:
            Logger.error(f"Error al crear copia de seguridad {e}")
            MDSnackbar(
                MDSnackbarText(text="Ha ocurrido un error", halign="left"),
                MDSnackbarSupportingText(text="No se pudo crear la copia de seguridad"),
                duration=8,
                pos_hint={"center_x": 0.5},
                y=dp(5),
                size_hint_x=0.8,
            ).open()

    def dialogo_cargar_copia(self, *args):
        dialogo_advertencia = MDDialog(
            MDDialogIcon(
                icon="alert",
                theme_icon_color="Custom",
                icon_color=self.widget_principal.AMARILLO,
            ),
            MDDialogHeadlineText(text="Importar Datos"),
            MDDialogSupportingText(
                text="Seleccione un archivo de copia de seguridad creado anteriormente para restablecer sus datos. Deberá reiniciar la aplicación.\n\n[b]Todos los datos actuales serán reemplazados.[/b]",
                halign="left",
                markup=True,
            ),
            size_hint_x=0.9,
            size_hint_y=None,
            radius=[dp(10), dp(10), dp(10), dp(10)],
            ripple_duration_in_fast=0,
            ripple_duration_in_slow=0,
            theme_focus_color="Custom",
            focus_color=[1, 1, 1, 0],
            padding="0dp",
            state_press=0,
        )
        botones = MDDialogButtonContainer(
            Widget(),
            MDButton(
                MDButtonText(
                    text="[b]Cancelar[/b]",
                    theme_text_color="Custom",
                    text_color=self.widget_principal.CYAN,
                    markup=True,
                ),
                on_release=lambda instance, dialogo=dialogo_advertencia: self.widget_principal.cerrar_dialogo(
                    dialogo
                ),
                style="text",
            ),
            MDButton(
                MDButtonText(
                    text="Seleccionar archivo",
                    theme_text_color="Custom",
                    text_color=self.widget_principal.CYAN,
                ),
                on_release=lambda instance, dialogo=dialogo_advertencia: self.seleccionar_archivo(
                    dialogo
                ),
                style="text",
            ),
            spacing="8dp",
        )
        dialogo_advertencia.add_widget(botones)
        dialogo_advertencia.open()

    def seleccionar_archivo(self, dialogo, *args):
        dialogo.dismiss()
        if platform == "android":
            self.chooser.choose_content("application/zip")
        else:
            self.choose_file = f"{RUTA_ARCHIVOS}/Copias de seguridad/Backup Unexum 18-01-2026 17-27-50.zip"
            self.cargar_copia()

    def cargar_copia(self, *args):
        carpeta_temporal_extraccion = join(RUTA_ARCHIVOS, "extraidos")
        carpeta_seguridad = join(RUTA_ARCHIVOS, "temp_seguridad")
        os.makedirs(carpeta_temporal_extraccion, exist_ok=True)
        os.makedirs(carpeta_seguridad, exist_ok=True)

        # Extraer los archivos en la carpeta de extraccion y verificar
        if self.choose_file.endswith(".zip"):
            shutil.unpack_archive(self.choose_file, carpeta_temporal_extraccion)

            nombres_archivos = os.listdir(carpeta_temporal_extraccion)
            valido = True
            for nombre_archivo in nombres_archivos:
                if not nombre_archivo.endswith(".json"):
                    valido = False

            if valido:
                # Mover a la carpeta de seguridad por ahora
                nombres_archivos = os.listdir(RUTA_DATOS)
                for nombre_archivo in nombres_archivos:
                    if nombre_archivo.endswith(".json"):
                        ruta_completa_origen = join(RUTA_DATOS, nombre_archivo)
                        shutil.move(ruta_completa_origen, carpeta_seguridad)

                # Movemos los archivos extraidos a la carpeta raiz
                try:
                    nombres_archivos = os.listdir(carpeta_temporal_extraccion)
                    for nombre_archivo in nombres_archivos:
                        if nombre_archivo.endswith(".json"):
                            ruta_completa_origen = os.path.join(
                                carpeta_temporal_extraccion, nombre_archivo
                            )
                            shutil.move(ruta_completa_origen, RUTA_DATOS)

                    self.copia_cargada = True
                    shutil.rmtree(carpeta_seguridad)
                    shutil.rmtree(carpeta_temporal_extraccion)
                    self.dialogo_carga_exitosa()

                except Exception as e:
                    Logger.error(f"Error al cargar copia de seguridad {e}")
                    # Devolvermos los archivos originales
                    nombres_archivos = os.listdir(carpeta_seguridad)
                    for nombre_archivo in nombres_archivos:
                        if nombre_archivo.endswith(".json"):
                            ruta_completa_origen = os.path.join(
                                carpeta_seguridad, nombre_archivo
                            )
                            shutil.move(carpeta_seguridad, RUTA_DATOS)

            else:
                MDSnackbar(
                    MDSnackbarText(text="Ha ocurrido un error", halign="left"),
                    MDSnackbarSupportingText(text="El archivo no es válido"),
                    duration=8,
                    pos_hint={"center_x": 0.5},
                    y=dp(5),
                    size_hint_x=0.8,
                ).open()
        else:
            MDSnackbar(
                MDSnackbarText(text="Ha ocurrido un error", halign="left"),
                MDSnackbarSupportingText(text="El archivo no es un .zip"),
                duration=8,
                pos_hint={"center_x": 0.5},
                y=dp(5),
                size_hint_x=0.8,
            ).open()

    @mainthread
    def dialogo_carga_exitosa(self, *args):
        dialogo_informacion = MDDialog(
            MDDialogIcon(
                icon="information",
                theme_icon_color="Custom",
                icon_color=self.widget_principal.AZUL_CLARO,
            ),
            MDDialogHeadlineText(text="[b]¡Copia Restaurada![b]", markup=True),
            MDDialogSupportingText(
                text="Por favor reinicia la aplicación",
                theme_font_size="Custom",
                font_size="14sp",
                markup=True,
                halign="left",
            ),
            size_hint_x=0.95,
            size_hint_y=None,
            radius=[dp(10), dp(10), dp(10), dp(10)],
            ripple_duration_in_fast=0,
            ripple_duration_in_slow=0,
            theme_focus_color="Custom",
            focus_color=[1, 1, 1, 0],
            padding="0dp",
            state_press=0,
            auto_dismiss=False,
        )
        boton = MDDialogButtonContainer(
            Widget(),
            MDButton(
                MDButtonText(
                    text="[b]Cerrar App[/b]",
                    theme_text_color="Custom",
                    text_color=self.widget_principal.CYAN,
                    markup=True,
                ),
                on_release=lambda instance, dialogo=dialogo_informacion: self.cerrar_app(
                    dialogo
                ),
                style="text",
            ),
        )
        dialogo_informacion.add_widget(boton)
        dialogo_informacion.open()

    def chooser_callback(self, choose_files):
        self.choose_file = None
        try:
            ss = SharedStorage()
            for choose in choose_files:
                path = ss.copy_from_shared(choose)
                if path:
                    self.choose_file = path
                    self.cargar_copia()
        except Exception as e:
            Logger.error(f"Error al elegir archivo desde chooser")

    def cerrar_app(self, *args):
        if platform == "android":
            mActivity.finishAndRemoveTask()
        else:
            self.stop()
            Window.close()

if __name__ == "__main__":
    MainApp().run()
