from django.core.management.base import BaseCommand

from geostore.models import Layer
from ...models import CrudView


class Command(BaseCommand):
    help = 'Create view for existing layers'

    def handle(self, *args, **options):
        for layer in Layer.objects.all():
            CrudView.objects.get_or_create(layer=layer,
                                           defaults={"name": layer.name, "order": 0})
