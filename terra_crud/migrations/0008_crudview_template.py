# Generated by Django 2.1 on 2019-08-21 15:48

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('template_model', '0001_initial'),
        ('terra_crud', '0007_auto_20190725_1256'),
    ]

    operations = [
        migrations.AddField(
            model_name='crudview',
            name='template',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='crud_views', to='template_model.Template'),
        ),
    ]