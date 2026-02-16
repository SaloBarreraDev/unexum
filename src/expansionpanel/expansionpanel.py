__all__ = (
    "FMDExpansionPanel",
    "FMDExpansionPanelContent",
    "FMDExpansionPanelHeader",
)

import os

from kivy.animation import Animation
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.properties import (
    NumericProperty,
    ObjectProperty,
    StringProperty,
    BooleanProperty,
)
from kivy.uix.boxlayout import BoxLayout

from kivymd import uix_path
from kivymd.theming import ThemableBehavior
from kivymd.uix.behaviors import BackgroundColorBehavior, DeclarativeBehavior

# CÓDIGO CORRECTO (Para tu proyecto local)
# Asegúrate de importar os al principio
import os

# Esto busca el archivo .kv en el mismo directorio que este archivo .py
with open(
    os.path.join(os.path.dirname(__file__), "expansionpanel.kv"),
    encoding="utf-8",
) as kv_file:
    Builder.load_string(kv_file.read())


class FMDExpansionPanelContent(
    DeclarativeBehavior, ThemableBehavior, BackgroundColorBehavior, BoxLayout
):
    _panel = ObjectProperty()

    def add_widget(self, widget, index=0, canvas=None):
        # El binding en el panel se encarga de actualizar la altura,
        # pero mantenemos el super() para que Kivy calcule el minimum_height
        return super().add_widget(widget, index=index, canvas=canvas)


class FMDExpansionPanelHeader(DeclarativeBehavior, BoxLayout):
    pass


class FMDExpansionPanel(DeclarativeBehavior, BoxLayout):
    opening_transition = StringProperty("out_cubic")
    opening_time = NumericProperty(0.2)
    closing_transition = StringProperty("out_sine")
    closing_time = NumericProperty(0.2)
    is_open = BooleanProperty(False)

    _header = ObjectProperty()
    _content = ObjectProperty()
    _original_content_height = NumericProperty()
    _allow_add_content = False
    _panel_is_process_opening = False

    __events__ = ("on_open", "on_close")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def on_open(self, *args) -> None:
        """Fired when a panel is opened."""

    def on_close(self, *args) -> None:
        """Fired when a panel is closed."""

    def set_chevron_down(self, instance) -> None:
        Animation(rotate_value_angle=-90, d=self.opening_time).start(instance)

    def set_chevron_up(self, instance) -> None:
        Animation(rotate_value_angle=0, d=self.closing_time).start(instance)

    def close(self, *args) -> None:
        def set_content_height(*args):
            anim_height = Animation(
                height=0,
                t=self.opening_transition,
                d=self.opening_time,
            )
            anim_height.bind(
                on_complete=lambda *args: self.remove_widget(self._content)
            )
            anim_height.start(self._content)
            self.is_open = False
            self.dispatch("on_close")

        anim_opacity = Animation(
            opacity=0,
            t=self.opening_transition,
            d=self.opening_time,
        )
        anim_opacity.bind(on_complete=set_content_height)
        anim_opacity.start(self._content)

    def open(self, *args) -> None:
        def set_content_opacity(*args):
            Animation(
                opacity=1,
                t=self.opening_transition,
                d=self.opening_time,
            ).start(self._content)
            self.is_open = True
            self._panel_is_process_opening = False
            self.dispatch("on_open")

        if not self._panel_is_process_opening:
            self._allow_add_content = True
            self._panel_is_process_opening = True
            
            # Aseguramos que la altura esté actualizada antes de abrir
            self._original_content_height = self._content.minimum_height
            
            self.add_widget(self._content)

            anim_height = Animation(
                height=self._original_content_height,
                t=self.opening_transition,
                d=self.opening_time,
            )
            anim_height.bind(on_complete=set_content_opacity)
            anim_height.start(self._content)

    def add_widget(self, widget, index=0, canvas=None):
        if isinstance(widget, FMDExpansionPanelHeader):
            self._header = widget
            return super().add_widget(widget, index=index, canvas=canvas)
        
        elif (
            isinstance(widget, FMDExpansionPanelContent)
            and not self._allow_add_content
        ):
            self._content = widget
            widget._panel = self
            
            # SOLUCIÓN CRÍTICA:
            # 1. Eliminamos el delay de 0.8s
            # 2. Bind directo a minimum_height para actualizaciones en tiempo real
            widget.bind(minimum_height=self._update_original_content_height)
            
            # Inicializamos la altura base
            Clock.schedule_once(
                lambda x: self._update_original_content_height(widget, widget.minimum_height), 
                0
            )
            
        elif (
            isinstance(widget, FMDExpansionPanelContent)
            and self._allow_add_content
        ):
            widget._panel = self
            return super().add_widget(widget, index=index, canvas=canvas)

    def _update_original_content_height(self, instance, value):
        """
        Actualiza la altura objetivo basándose en el minimum_height real del contenido.
        Elimina la resta arbitraria de dp(88).
        """
        self._original_content_height = value
        
        # Si el panel está abierto y el contenido cambia dinámicamente,
        # actualizamos la altura visual en tiempo real.
        if self.is_open and self._content:
            self._content.height = value