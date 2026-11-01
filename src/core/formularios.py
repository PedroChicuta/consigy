"""Padrão visual dos formulários (ADR 0010): todo form renderiza com Bootstrap sem
declarar classes CSS nos `forms.py`."""

from django.forms import BoundField, CheckboxInput, Select, SelectMultiple, Textarea
from django.forms.renderers import TemplatesSetting

# Widgets que ocupam a linha inteira da grade; os demais ficam em meia largura.
_LARGURA_TOTAL = (Textarea, CheckboxInput)


def _classe_bootstrap(widget):
    if isinstance(widget, CheckboxInput):
        return 'form-check-input'
    if isinstance(widget, (Select, SelectMultiple)):
        return 'form-select'
    return 'form-control'


class CampoBootstrap(BoundField):
    """Acrescenta a classe Bootstrap do widget e `is-invalid` quando há erro."""

    def build_widget_attrs(self, attrs, widget=None):
        attrs = super().build_widget_attrs(attrs, widget)
        widget = widget or self.field.widget
        if widget.is_hidden:
            return attrs
        classes = [widget.attrs.get('class', ''), attrs.get('class', ''), _classe_bootstrap(widget)]
        if self.errors:
            classes.append('is-invalid')
        attrs['class'] = ' '.join(dict.fromkeys(' '.join(classes).split()))
        return attrs

    @property
    def classe_coluna(self):
        return 'col-12' if isinstance(self.field.widget, _LARGURA_TOTAL) else 'col-12 col-md-6'


class RendererBootstrap(TemplatesSetting):
    form_template_name = 'formularios/form.html'
    field_template_name = 'formularios/campo.html'
    bound_field_class = CampoBootstrap
