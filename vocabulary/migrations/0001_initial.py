# Generated by Django 4.2.14 on 2025-07-07 04:11

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Flashcard',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('word', models.CharField(max_length=255, unique=True)),
                ('part_of_speech', models.CharField(blank=True, max_length=50, null=True)),
                ('general_synonyms', models.TextField(blank=True, help_text='Comma-separated list of general synonyms', null=True)),
                ('general_antonyms', models.TextField(blank=True, help_text='Comma-separated list of general antonyms', null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'ordering': ['word'],
            },
        ),
        migrations.CreateModel(
            name='Pronunciation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('text', models.CharField(max_length=255)),
                ('audio_url', models.URLField(blank=True, max_length=500, null=True)),
                ('flashcard', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='pronunciations', to='vocabulary.flashcard')),
            ],
        ),
        migrations.CreateModel(
            name='Definition',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('english_definition', models.TextField()),
                ('vietnamese_definition', models.TextField()),
                ('definition_synonyms', models.TextField(blank=True, help_text='Comma-separated list of synonyms for this definition', null=True)),
                ('definition_antonyms', models.TextField(blank=True, help_text='Comma-separated list of antonyms for this definition', null=True)),
                ('flashcard', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='definitions', to='vocabulary.flashcard')),
            ],
        ),
    ]
