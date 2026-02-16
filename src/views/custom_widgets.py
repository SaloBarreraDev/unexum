from kivymd.app import MDApp
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
from expansionpanel import FMDExpansionPanel
from kivy.uix.behaviors import ButtonBehavior
from kivymd.uix.behaviors import RotateBehavior
from kivymd.uix.list import MDListItemTrailingIcon
from kivy.properties import (StringProperty, ObjectProperty, BooleanProperty,
    ColorProperty)

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
class BoxConRippleIndice(RectangularRippleBehavior, MDRelativeLayout):
    ripple_duration_in_fast = 0.1
    ripple_duration_in_slow = 0
    ripple_duration_out = 0.1
    ripple_color = [0.5, 0.5, 0.5, 0.1]

class LabelListaIndice(MDLabel):
    pass

class CampoTextoListaIndice(MDTextField):
    pass

# Widgets de pensum Custom
class BoxConRipplePensum(RectangularRippleBehavior, MDRelativeLayout):
    ripple_duration_in_fast = 0.1
    ripple_duration_in_slow = 0
    ripple_duration_out = 0.1
    ripple_color = [0.5, 0.5, 0.5, 0.1]

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
