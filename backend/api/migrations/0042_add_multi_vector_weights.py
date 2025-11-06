# Generated manually for multi-vector weights configuration
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0041_searchthresholdsetting'),
    ]

    operations = [
        migrations.AddField(
            model_name='searchthresholdsetting',
            name='title_weight',
            field=models.IntegerField(
                default=60,
                help_text='標題向量的權重百分比（0-100），用於多向量搜尋',
                verbose_name='標題權重'
            ),
        ),
        migrations.AddField(
            model_name='searchthresholdsetting',
            name='content_weight',
            field=models.IntegerField(
                default=40,
                help_text='內容向量的權重百分比（0-100），用於多向量搜尋',
                verbose_name='內容權重'
            ),
        ),
    ]
