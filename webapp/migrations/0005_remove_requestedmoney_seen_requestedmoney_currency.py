# Generated by Django 4.2.11 on 2024-03-14 14:23

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("webapp", "0004_requestedmoney"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="requestedmoney",
            name="seen",
        ),
        migrations.AddField(
            model_name="requestedmoney",
            name="currency",
            field=models.CharField(default="GBP", max_length=3),
        ),
    ]
