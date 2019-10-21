# Generated by Django 2.2.6 on 2019-10-17 09:50

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('geostore', '0032_auto_20191016_0844'),
        ('terra_geocrud', '0026_auto_20191014_0919'),
    ]

    operations = [
        migrations.CreateModel(
            name='AttachmentCategory',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, unique=True)),
                ('pictogram', models.ImageField(blank=True, null=True, upload_to='crud/attachments_category/pictograms')),
            ],
            options={
                'verbose_name': 'Attachment category',
                'verbose_name_plural': 'Attachment categories',
            },
        ),
        migrations.CreateModel(
            name='FeaturePicture',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('legend', models.CharField(max_length=250)),
                ('image', models.ImageField(storage='django.core.files.storage.FileSystemStorage', upload_to='')),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='terra_geocrud.AttachmentCategory')),
                ('feature', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='pictures', to='geostore.Feature')),
            ],
            options={
                'verbose_name': 'Feature picture',
                'verbose_name_plural': 'Feature pictures',
                'ordering': ('feature', 'category', '-updated_at'),
            },
        ),
        migrations.CreateModel(
            name='FeatureAttachment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('legend', models.CharField(max_length=250)),
                ('file', models.FileField(storage='django.core.files.storage.FileSystemStorage', upload_to='')),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='terra_geocrud.AttachmentCategory')),
                ('feature', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='attachments', to='geostore.Feature')),
            ],
            options={
                'verbose_name': 'Feature attachment',
                'verbose_name_plural': 'Feature attachments',
                'ordering': ('feature', 'category', '-updated_at'),
            },
        ),
    ]