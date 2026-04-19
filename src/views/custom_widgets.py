from kivymd.app import MDApp
from src.utils import interpolar_nota
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.behaviors import CommonElevationBehavior, RectangularRippleBehavior
from kivymd.uix.relativelayout import MDRelativeLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.textfield import MDTextField
from kivymd.uix.selectioncontrol import MDCheckbox
from kivymd.uix.behaviors.focus_behavior import FocusBehavior
from kivy.uix.recycleview import RecycleView
from kivy.uix.recycleview.layout import LayoutSelectionBehavior
from kivy.uix.recycleview.views import RecycleDataViewBehavior
from kivy.uix.recycleboxlayout import RecycleBoxLayout
from kivymd.uix.boxlayout import MDBoxLayout
from src.expansionpanel import FMDExpansionPanel
from kivy.uix.behaviors import ButtonBehavior
from kivymd.uix.behaviors import RotateBehavior
from kivymd.uix.list import MDListItemTrailingIcon
from kivy.properties import (StringProperty, ObjectProperty, BooleanProperty,
    ColorProperty)
from kivymd.uix.snackbar import MDSnackbar, MDSnackbarText, MDSnackbarSupportingText
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.uix.relativelayout import RelativeLayout
import threading
class BoxLayoutElevated(
    RectangularRippleBehavior, CommonElevationBehavior, MDRelativeLayout
):
    def __init__(self, **kwargs):
        self.ripple_duration_in_fast = 0.1
        self.ripple_duration_in_slow = 0
        self.ripple_duration_out = 0.1
        self.ripple_color = [0.5, 0.5, 0.5, 0.1]
        super().__init__(**kwargs)

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            hijo = self.children[0]
            self.call_ripple_animation_methods(touch)
            app = MDApp.get_running_app()
            widget_principal = app.root
            if (
                hijo.text == "-"
                or hijo.text == "CUM LAUDE"
                or hijo.text == "SUMMA CUM LAUDE"
            ):
                widget_principal.dialogo_mencion_honorifica()
            elif "/" in hijo.text:
                pass
            else:
                widget_principal.dialogo_ubicacion_semestre()
            return True

class CustomMDScrollView(MDScrollView):
    def stop_scroll(self, touch):
        if self.bar_width and self.collide_point(touch.x, touch.y):
            if self.effect_y:
                self.effect_y.velocity = 0

class BoxConRipple(RectangularRippleBehavior, MDRelativeLayout):
    ripple_duration_in_fast = 0.1
    ripple_duration_in_slow = 0
    ripple_duration_out = 0.1
    ripple_color = [0.5, 0.5, 0.5, 0.1]

# Widgets de indice custom
class BoxConRippleIndice(RecycleDataViewBehavior, RectangularRippleBehavior, RelativeLayout):
    nombre_materia = StringProperty("")
    codigo_materia = StringProperty("")
    uc = StringProperty("")
    color_fondo = ColorProperty()
    nota = ObjectProperty()
    index = 0
    ripple_duration_in_fast = 0.1
    ripple_duration_in_slow = 0
    ripple_duration_out = 0.1
    ripple_color = [0.5, 0.5, 0.5, 0.1]
    _is_recycling = False

    def on_text(self, text, focus, instance):
        app = MDApp.get_running_app()
        wp = app.widget_principal
        if self._is_recycling:
            return

        lista_materias = wp.get_materias()
        materia = wp.buscar_por_codigo(self.codigo_materia)
        if not focus:
            if text == "":
                materia.nota = ""
                wp.ids.rv_indice.data[self.index]["nota"] = ""
                instance.text = ""
                wp.calcular_indice()
                wp.guardar_datos(lista_materias)
            else:
                if wp.es_numero(text):
                    if float(text) >= 1 and float(text) <= 9:
                        nota_redondeada = round(float(text), 1)
                        materia.nota = nota_redondeada
                        wp.ids.rv_indice.data[self.index]["nota"] = nota_redondeada
                        instance.text = ""
                        wp.calcular_indice()
                        wp.guardar_datos(lista_materias)
                    elif float(text) > 9 and float(text) <= 100:
                        nota_interpolada = interpolar_nota(round(float(text)))
                        materia.nota = nota_interpolada
                        wp.ids.rv_indice.data[self.index]["nota"] = nota_interpolada
                        instance.text = ""
                        wp.calcular_indice()
                        wp.guardar_datos(lista_materias)
                    else:
                        materia.nota = ""
                        wp.ids.rv_indice.data[self.index]["nota"] = ""
                        instance.text = ""
                        wp.calcular_indice()
                        wp.guardar_datos(lista_materias)
                        MDSnackbar(
                            MDSnackbarText(text='Nota inválida', halign="left"),
                            MDSnackbarSupportingText(
                                text="La nota debe estar entre 1-9 o 9-100"
                            ),
                            duration=5,
                            pos_hint={"center_x": 0.5},
                            y=dp(5),
                            size_hint_x=0.8,
                        ).open()
                else:
                    materia.nota = ""
                    wp.ids.rv_indice.data[self.index]["nota"] = ""
                    instance.text = ""
                    wp.calcular_indice()
                    wp.guardar_datos(lista_materias)
                    MDSnackbar(
                            MDSnackbarText(text='Nota inválida', halign="left"),
                            MDSnackbarSupportingText(
                                text="La nota debe ser un número"
                            ),
                            duration=5,
                            pos_hint={"center_x": 0.5},
                            y=dp(5),
                            size_hint_x=0.8,
                        ).open()

            wp.ids.rv_indice.refresh_from_data()

    def refresh_view_attrs(self, rv, index, data):
        self._is_recycling = True # Bloqueo de guardado accidental
        self.index = index
        super(BoxConRippleIndice, self).refresh_view_attrs(rv, index, data)
        
        for child in self.children:
            if isinstance(child, CampoTextoListaIndice):
                child.focus = False
                
        self._is_recycling = False # Desbloqueamos el guardado

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            app = MDApp.get_running_app()
            wp = app.widget_principal
            wp.ver_evaluaciones(self, touch, wp.buscar_por_codigo(self.codigo_materia), True)
            super().on_touch_down(touch)
            return True
        return super().on_touch_down(touch)

class LabelListaIndice(MDLabel):
    pass

class CampoTextoListaIndice(MDTextField):
    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            box = self.parent
            target_codigo = box.codigo_materia if hasattr(box, 'codigo_materia') else None
            rv_layout = box.parent if box else None
            if rv_layout:
                for fila in rv_layout.children:
                    for widget in fila.children:
                        if isinstance(widget, CampoTextoListaIndice) and widget != self and widget.focus:
                            widget.focus = False 

            super().on_touch_down(touch)

            if target_codigo and rv_layout:
                Clock.schedule_once(lambda dt: self._restaurar_foco(target_codigo, rv_layout), 0.05)
                
            return True 
            
        return super().on_touch_down(touch)

    def on_text_validate(self):
        box = self.parent
        if not hasattr(box, 'index'):
            return
            
        current_index = box.index
        target_index = current_index + 1
        
        app = MDApp.get_running_app()
        rv = app.widget_principal.ids.rv_indice
        
        pixels_to_scroll = 0
        while target_index < len(rv.data):
            vista = rv.data[target_index].get('viewclass')
            if vista == 'SemestreIndice':
                pixels_to_scroll += dp(45) 
                target_index += 1
            elif vista == 'BoxConRippleIndice':
                pixels_to_scroll += dp(64) 
                break
            else:
                target_index += 1
                
        if target_index >= len(rv.data):
            self.focus = False
            return
            
        target_codigo = rv.data[target_index].get('codigo_materia')
        rv_layout = box.parent
        
        self.focus = False
        
        scrollable_height = rv.layout_manager.height - rv.height
        if scrollable_height > 0:
            delta_y = pixels_to_scroll / scrollable_height
            rv.scroll_y = max(0.0, rv.scroll_y - delta_y) 
            
        Clock.schedule_once(lambda dt: self._restaurar_foco(target_codigo, rv_layout), 0.1)
    def _restaurar_foco(self, target_codigo, rv_layout):
        for fila in rv_layout.children:
            if hasattr(fila, 'codigo_materia') and fila.codigo_materia == target_codigo:
                for widget in fila.children:
                    if isinstance(widget, CampoTextoListaIndice):
                        widget.focus = True
                        return
        
# Widgets de pensum Custom
class BoxConRipplePensum(RecycleDataViewBehavior, RectangularRippleBehavior, MDRelativeLayout):
    nombre_materia = StringProperty("")
    codigo_materia = StringProperty("")
    uc = StringProperty("")
    color_fondo = ColorProperty()
    active = BooleanProperty()
    index = 0
    texto_label = StringProperty("")
    ripple_duration_in_fast = 0.1
    ripple_duration_in_slow = 0
    ripple_duration_out = 0.1
    ripple_color = [0.5, 0.5, 0.5, 0.1]
    
    # Banderas de seguridad
    _is_recycling = False
    _bloqueo_global_toques = False 

    def aprobar_materia(self, value, codigo, instance):
        if self._is_recycling or BoxConRipplePensum._bloqueo_global_toques:
            return

        BoxConRipplePensum._bloqueo_global_toques = True
        
        Clock.schedule_once(lambda dt: self._procesar_aprobacion(value, codigo, instance))

    def _procesar_aprobacion(self, value, codigo, instance):
        try:
            app = MDApp.get_running_app()
            wp = app.widget_principal
            materia = wp.buscar_por_codigo(codigo)
            lista_materias = wp.get_materias()

            indice_real = wp.mapa_indices_pensum.get(codigo)
            if indice_real is None:
                return

            if value:
                if materia.disponible:
                    materia.aprobada = True
                    wp.ids.rv_pensum.data[indice_real]["active"] = True
                    wp.ids.rv_pensum.data[indice_real]["color_fondo"] = wp.VERDE
                    
                    wp.unidades_aprobadas_y_totales()
                    wp.actualizar_pensum(materia.codigo) 
                    wp.guardar_datos(lista_materias)
                else:
                    self._is_recycling = True
                    instance.active = False 
                    wp.ids.rv_pensum.data[indice_real]["active"] = False
                    self._is_recycling = False
            else:
                materia.aprobada = False
                color = wp.AMARILLO if materia.disponible else wp.color_fondo_claro
                wp.ids.rv_pensum.data[indice_real]["active"] = False
                wp.ids.rv_pensum.data[indice_real]["color_fondo"] = color
                
                wp.unidades_aprobadas_y_totales()
                wp.desactualizar_pensum(materia.codigo)
                wp.guardar_datos(lista_materias)
        finally:
            BoxConRipplePensum._bloqueo_global_toques = False

    def refresh_view_attrs(self, rv, index, data):
        self._is_recycling = True
        self.index = index
        self.active = data.get('active', False)
        super(BoxConRipplePensum, self).refresh_view_attrs(rv, index, data)
        for child in self.children:
            if isinstance(child, MDCheckbox):
                if child.active != self.active:
                    child.active = self.active
                break
        self._is_recycling = False

    def on_touch_down(self, touch):
        if BoxConRipplePensum._bloqueo_global_toques:
            return False
            
        if self.collide_point(*touch.pos) and touch.is_double_tap:
            app = MDApp.get_running_app()
            wp = app.widget_principal
            materia = wp.buscar_por_codigo(self.codigo_materia)
            wp.mostrar_informacion_materia(materia, False, materia.semestre)
            super().on_touch_down(touch)
            return True
            
        return super().on_touch_down(touch)

class LabelListaPensum(MDLabel):
    pass

class CheckBoxPensum(MDCheckbox):
    pass

# Widgets de horario Custom
class CampoTextoHorario(MDTextField):
    pass

# Widgets Customs para recycle view añadir materias inscritas:
class SelectableRecycleBoxLayout(
    FocusBehavior, LayoutSelectionBehavior, RecycleBoxLayout
):
    pass

class SelectableLabel(RecycleDataViewBehavior, MDLabel):
    """Add selection support to the Label"""

    index = None
    selected = BooleanProperty(False)
    selectable = BooleanProperty(True)

    def refresh_view_attrs(self, rv, index, data):
        """Catch and handle the view changes"""
        super(SelectableLabel, self).refresh_view_attrs(rv, index, data)
        self.index = index
        layout_manager = rv.layout_manager
        if layout_manager:
            is_selected_in_layout = self.index in layout_manager.selected_nodes
            if self.selected != is_selected_in_layout:
                self.apply_selection(rv, self.index, is_selected_in_layout)

    def on_touch_down(self, touch):
        """Add selection on touch down"""
        if super(SelectableLabel, self).on_touch_down(touch):
            return True
        if self.collide_point(*touch.pos) and self.selectable:
            return self.parent.select_with_touch(self.index, touch)

    def apply_selection(self, rv, index, is_selected):
        """Respond to the selection of items in the view."""
        self.selected = is_selected
        rv.data[index]["materia"].inscrita = is_selected

class RV(RecycleView):
    def __init__(self, lista_materias, **kwargs):
        super(RV, self).__init__(**kwargs)

        self.lista_materias = []
        for materia in lista_materias:
            if materia.disponible and not materia.aprobada:
                self.lista_materias.append(materia)
            else:
                if materia.inscrita:
                    materia.inscrita = False

        self.data = [
            {"text": materia.nombre, "materia": materia}
            for materia in self.lista_materias
        ]
        if self.layout_manager:
            for index, data_item in enumerate(self.data):
                if data_item.get("materia").inscrita:
                    self.layout_manager.select_node(index)

#Recycle views horario
class SelectableLabelHorario(RecycleDataViewBehavior, MDLabel):
    """Add selection support to the Label"""

    index = None
    selected = BooleanProperty(False)
    selectable = BooleanProperty(True)

    def refresh_view_attrs(self, rv, index, data):
        """Catch and handle the view changes"""
        super(SelectableLabelHorario, self).refresh_view_attrs(rv, index, data)
        self.index = index
        layout_manager = rv.layout_manager
        if layout_manager:
            is_selected_in_layout = self.index in layout_manager.selected_nodes
            if self.selected != is_selected_in_layout:
                self.apply_selection(rv, self.index, is_selected_in_layout)

    def on_touch_down(self, touch):
        """Add selection on touch down"""
        if super(SelectableLabelHorario, self).on_touch_down(touch):
            return True
        if self.collide_point(*touch.pos) and self.selectable:
            return self.parent.select_with_touch(self.index, touch)

    def apply_selection(self, rv, index, is_selected):
        """Respond to the selection of items in the view."""
        self.selected = is_selected
        materia = rv.data[index]["materia"]
        if is_selected:
            if materia.codigo not in rv.lista_horario:
                rv.lista_horario.append(materia.codigo)
        else:
            if materia.codigo in rv.lista_horario:
                rv.lista_horario.remove(materia.codigo)

class RVHorario(RecycleView):
    def __init__(self, lista_materias, lista_horario, disponible,**kwargs):
        super(RVHorario, self).__init__(**kwargs)
        self.lista_horario = lista_horario
        self.lista_materias = []
        if disponible:
            for materia in lista_materias:
                if materia.disponible and not materia.aprobada:
                    self.lista_materias.append(materia)
        else:
            self.lista_materias = lista_materias

        self.data = [
            {"text": materia.nombre, "materia": materia}
            for materia in self.lista_materias
        ]
        if self.layout_manager:
            for index, data_item in enumerate(self.data):
                if data_item.get("materia").codigo in lista_horario:
                    self.layout_manager.select_node(index)

# Layouts customs de inicio
class BoxConRippleInicio(RectangularRippleBehavior, MDBoxLayout):
    def __init__(self, *args, **kwargs):
        self.ripple_duration_in_fast = 0.1
        self.ripple_duration_in_slow = 0
        self.ripple_duration_out = 0.1
        self.ripple_color = [0.5, 0.5, 0.5, 0.1]
        super(BoxConRippleInicio, self).__init__(*args, **kwargs)

#Clases customs de horario
class ExpansionPanelItem(FMDExpansionPanel):
    nombre_materia = StringProperty("")
    def __init__(self, materia, **kwargs):
        super(ExpansionPanelItem, self).__init__(**kwargs)
        self.materia = materia
        self.nombre_materia = materia.nombre
        
class TrailingPressedIconButton(ButtonBehavior, RotateBehavior, MDListItemTrailingIcon):
    pass

class Seccion(CommonElevationBehavior, MDRelativeLayout):
    nro_seccion = StringProperty("")
    profesor = StringProperty("")
    dias = StringProperty("")
    estado = ObjectProperty(True)
    aula = StringProperty("")
    def __init__(self, materia, nro_seccion, profesor, dias, estado, aula, **kwargs):
        super().__init__(**kwargs)
        self.materia = materia
        self.nro_seccion = nro_seccion
        self.profesor = profesor
        self.dias = dias
        self.estado = estado
        self.aula = aula


#RV custom indice y pensum
class RVIndice(RecycleView):
    def __init__(self, **kwargs):
        super(RVIndice, self).__init__(**kwargs)
        self.data = []

class SemestreIndice(MDBoxLayout):
    texto_semestre = StringProperty("")
    color_fondo = ColorProperty()

class RVPensum(RecycleView):
    def __init__(self, **kwargs):
        super(RVPensum, self).__init__(**kwargs)
        self.data = []

class SemestrePensum(MDBoxLayout):
    texto_semestre = StringProperty("")
    color_fondo = ColorProperty()

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos) and touch.is_double_tap:
            app = MDApp.get_running_app()
            wp = app.widget_principal
            wp.mostrar_informacion_materia("materia", True, self.texto_semestre)
            super().on_touch_down(touch)
            return True
        return super().on_touch_down(touch)


class BoxConRippleElectivas(RectangularRippleBehavior, MDRelativeLayout):
    ripple_duration_in_fast = 0.1
    ripple_duration_in_slow = 0
    ripple_duration_out = 0.1
    ripple_color = [0.5, 0.5, 0.5, 0.1]
    _is_recycling = False