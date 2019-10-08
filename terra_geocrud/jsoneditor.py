from django_json_widget.widgets import JSONEditorWidget


class JSONEditorWidget(JSONEditorWidget):
    """ Override media infos ith compliant django style """
    class Media(JSONEditorWidget.Media):
        css = {'all': ('dist/jsoneditor.min.css',)}
        js = ('dist/jsoneditor.min.js',)
