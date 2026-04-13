from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0008_alter_about_options_alter_category_options_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='post',
            name='body_html_en',
            field=models.TextField(blank=True, default='', editable=False, verbose_name='Conteúdo HTML (Inglês)'),
        ),
        migrations.AddField(
            model_name='post',
            name='body_html_es',
            field=models.TextField(blank=True, default='', editable=False, verbose_name='Conteúdo HTML (Espanhol)'),
        ),
        migrations.AddField(
            model_name='post',
            name='body_markdown_en',
            field=models.TextField(blank=True, default='', verbose_name='Conteúdo Markdown (Inglês)'),
        ),
        migrations.AddField(
            model_name='post',
            name='body_markdown_es',
            field=models.TextField(blank=True, default='', verbose_name='Conteúdo Markdown (Espanhol)'),
        ),
        migrations.AddField(
            model_name='post',
            name='summary_en',
            field=models.TextField(blank=True, default='', verbose_name='Resumo (Inglês)'),
        ),
        migrations.AddField(
            model_name='post',
            name='summary_es',
            field=models.TextField(blank=True, default='', verbose_name='Resumo (Espanhol)'),
        ),
        migrations.AddField(
            model_name='post',
            name='title_en',
            field=models.CharField(blank=True, default='', max_length=255, verbose_name='Título (Inglês)'),
        ),
        migrations.AddField(
            model_name='post',
            name='title_es',
            field=models.CharField(blank=True, default='', max_length=255, verbose_name='Título (Espanhol)'),
        ),
    ]
