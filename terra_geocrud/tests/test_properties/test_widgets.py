from django.test import TestCase

from geostore.tests.factories import FeatureFactory
from terra_geocrud.properties import widgets


class BaseWidgetTestCase(TestCase):
    def setUp(self) -> None:
        self.property_key = 'logo'
        self.feature_with_file_name = FeatureFactory(
            properties={
                self.property_key: 'data=image/png;name=toto.png;base64,xxxxxxxxxxxxxxxxxxxxxxxxxx=='
            }
        )

    def test_render_raise_exception(self):
        with self.assertRaises(NotImplementedError):
            widget = widgets.BaseWidget(feature=self.feature_with_file_name, prop=self.property_key)
            widget.render()


class GetWidgetChoicesTestCase(TestCase):
    def setUp(self) -> None:
        self.choices = widgets.get_widgets_choices()
        self.class_names = [choice[1] for choice in self.choices]

    def test_basewidget_not_in_choices(self):
        # Base Widget should NOT be in the list
        self.assertNotIn('BaseWidget', self.class_names)

    def test_other_widget_are_presents(self):
        self.assertIn('FileAhrefWidget', self.class_names)
        self.assertIn('DataUrlToImgWidget', self.class_names)


class DataUrlToImgWidgetTestCase(TestCase):
    def setUp(self) -> None:
        self.property_key = 'logo'
        self.feature = FeatureFactory(
            properties={
                self.property_key: 'data=application/pdf;name=toto.pdf;base64,xxxxxxxxxxxxxxxxxxxxxxxxxx=='
            }
        )

    def test_rendering_without_args(self):
        widget = widgets.DataUrlToImgWidget(feature=self.feature, prop=self.property_key)
        content = widget.render()

        # should looks like as img tag
        self.assertTrue(content.startswith('<img src='))
        self.assertTrue(content.endswith('/>'))

    def test_rendering_wit_args(self):
        args = {"attrs": {"target": "_blank", "width": '500px', "height": '200px'}}
        widget = widgets.DataUrlToImgWidget(feature=self.feature, prop=self.property_key, args=args)
        content = widget.render()

        # should looks like as img tag
        self.assertTrue(content.startswith('<img src='))
        self.assertTrue(content.endswith('/>'))

        # args should be present as html attributes
        for key, value in args.get('attrs').items():
            self.assertIn(f'{key}="{value}"', content)


class FileAhrefWidgetTestCase(TestCase):
    def setUp(self) -> None:
        self.property_key = 'logo'
        self.feature = FeatureFactory(
            properties={
                self.property_key: 'data=image/png;name=toto.png;base64,xxxxxxxxxxxxxxxxxxxxxxxxxx=='
            }
        )

    def test_rendering_without_args(self):
        widget = widgets.FileAhrefWidget(feature=self.feature, prop=self.property_key)
        content = widget.render()

        # should looks like as a tag
        self.assertTrue(content.startswith('<a href='), content)
        self.assertTrue(content.endswith('</a>'))

    def test_rendering_wit_args(self):
        args = {"attrs": {"target": "_blank", "width": '500px', "height": '200px'}}
        widget = widgets.FileAhrefWidget(feature=self.feature, prop=self.property_key, args=args)
        content = widget.render()

        # should looks like as a tag
        self.assertTrue(content.startswith('<a href='), content)
        self.assertTrue(content.endswith('</a>'))

        # args should be present as html attributes
        for key, value in args.get('attrs').items():
            self.assertIn(f'{key}="{value}"', content)


class DateFormatWidgetTestCase(TestCase):
    def setUp(self) -> None:
        self.property_key = 'date'
        self.feature = FeatureFactory(
            properties={
                self.property_key: '1999-12-31'
            }
        )

    def test_rendering_without_args(self):
        widget = widgets.DateFormatWidget(feature=self.feature, prop=self.property_key)
        content = widget.render()

        # should formatted as SHORT_DATE_FORMAT
        self.assertEqual(content, '12/31/1999')

    def test_rendering_wit_args(self):
        args = {"format": "d/m/Y"}
        widget = widgets.DateFormatWidget(feature=self.feature, prop=self.property_key, args=args)
        content = widget.render()

        self.assertEqual(content, '31/12/1999')
