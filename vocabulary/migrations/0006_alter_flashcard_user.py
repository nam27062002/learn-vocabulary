# Generated by Django 4.2.23 on 2025-07-08 06:15

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('vocabulary', '0005_flashcard_user_alter_flashcard_word_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='flashcard',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='flashcards', to=settings.AUTH_USER_MODEL),
        ),
    ]
