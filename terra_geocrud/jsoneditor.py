from django_json_widget.widgets import JSONEditorWidget


class JSONEditorWidget(JSONEditorWidget):
    """
    Override media infos ith compliant django style
    Wait for https://github.com/jmrivas86/django-json-widget/pull/23 merge
    """
    class Media(JSONEditorWidget.Media):
        css = {'all': ('dist/jsoneditor.min.css',)}
        js = ('dist/jsoneditor.min.js',)
