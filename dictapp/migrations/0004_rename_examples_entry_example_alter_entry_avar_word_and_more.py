# Generated by Django 5.1.7 on 2025-03-26 23:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dictapp', '0003_audioentry'),
    ]

    operations = [
        migrations.RenameField(
            model_name='entry',
            old_name='examples',
            new_name='example',
        ),
        migrations.AlterField(
            model_name='entry',
            name='avar_word',
            field=models.CharField(max_length=255),
        ),
        migrations.AlterField(
            model_name='entry',
            name='english_translations',
            field=models.TextField(),
        ),
    ]
