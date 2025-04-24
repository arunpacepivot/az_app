from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='StoredFile',
            fields=[
                ('file_id', models.CharField(max_length=64, primary_key=True)),
                ('filename', models.CharField(max_length=255)),
                ('blob_name', models.CharField(blank=True, max_length=255, null=True)),
                ('blob_url', models.URLField(blank=True, max_length=500, null=True)),
                ('local_path', models.CharField(blank=True, max_length=255, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('expires_at', models.DateTimeField()),
                ('access_count', models.IntegerField(default=0)),
                ('is_blob', models.BooleanField(default=False)),
            ],
            options={
                'app_label': 'core',
                'indexes': [models.Index(fields=['expires_at']), models.Index(fields=['filename'])],
            },
        ),
    ] 