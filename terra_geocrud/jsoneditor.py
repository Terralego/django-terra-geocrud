from django_json_widget.widgets import JSONEditorWidget as BaseJSONEditorWidget


class JSONEditorWidget(BaseJSONEditorWidget):
    """
    Override media infos ith compliant django style
    Wait for https://github.com/jmrivas86/django-json-widget/pull/23 merge
    """
    class Media(BaseJSONEditorWidget.Media):
        css = {'all': ('dist/jsoneditor.min.css',)}
        js = ('dist/jsoneditor.min.js',)
