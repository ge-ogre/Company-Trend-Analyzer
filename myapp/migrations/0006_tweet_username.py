# Generated by Django 4.1.1 on 2023-04-25 03:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0005_add_stock_model'),
    ]

    operations = [
        migrations.AddField(
            model_name='tweet',
            name='username',
            field=models.CharField(default='', max_length=255),
        ),
    ]
