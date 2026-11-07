import django.db.models.deletion
from django.db import migrations, models


def move_topics_to_subforums(apps, schema_editor):
    """Каждой главной теме — подтема «Общее обсуждение»; туда переносятся существующие публикации."""
    Category = apps.get_model("forum", "Category")
    Subforum = apps.get_model("forum", "Subforum")
    Topic = apps.get_model("forum", "Topic")
    for cat in Category.objects.all():
        sub = Subforum.objects.create(category=cat, title="Общее обсуждение", slug="general", order=0)
        Topic.objects.filter(category=cat).update(subforum=sub)


class Migration(migrations.Migration):

    dependencies = [
        ("forum", "0002_category_access"),
    ]

    operations = [
        migrations.CreateModel(
            name="Subforum",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=100, verbose_name="название")),
                ("slug", models.SlugField(verbose_name="адрес")),
                ("description", models.CharField(blank=True, max_length=255, verbose_name="описание")),
                ("order", models.PositiveSmallIntegerField(default=0, verbose_name="порядок")),
                ("category", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="subforums",
                                               to="forum.category", verbose_name="главная тема")),
            ],
            options={
                "verbose_name": "подтема",
                "verbose_name_plural": "подтемы",
                "ordering": ["category__order", "order", "title"],
                "constraints": [models.UniqueConstraint(fields=("category", "slug"), name="unique_subforum_slug")],
            },
        ),
        migrations.AddField(
            model_name="topic",
            name="subforum",
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name="topics",
                                    to="forum.subforum", verbose_name="подтема"),
        ),
        migrations.AddField(
            model_name="topic",
            name="kind",
            field=models.CharField(choices=[("discussion", "Обсуждение"), ("question", "Вопрос")],
                                   default="discussion", max_length=12, verbose_name="тип"),
        ),
        migrations.AddField(
            model_name="topic",
            name="solution",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                                    related_name="+", to="forum.post", verbose_name="лучший ответ"),
        ),
        migrations.RunPython(move_topics_to_subforums, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="topic",
            name="subforum",
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="topics",
                                    to="forum.subforum", verbose_name="подтема"),
        ),
        migrations.AlterField(
            model_name="topic",
            name="category",
            field=models.ForeignKey(editable=False, on_delete=django.db.models.deletion.CASCADE, related_name="topics",
                                    to="forum.category", verbose_name="главная тема"),
        ),
        migrations.AlterModelOptions(
            name="category",
            options={"ordering": ["order", "title"], "verbose_name": "главная тема", "verbose_name_plural": "главные темы"},
        ),
        migrations.AlterModelOptions(
            name="topic",
            options={"ordering": ["-is_pinned", "-last_activity"], "verbose_name": "публикация",
                     "verbose_name_plural": "публикации"},
        ),
        migrations.AlterModelOptions(
            name="categoryaccess",
            options={"verbose_name": "доступ к главной теме", "verbose_name_plural": "доступ к главным темам"},
        ),
        migrations.AlterField(
            model_name="post",
            name="topic",
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="posts",
                                    to="forum.topic", verbose_name="публикация"),
        ),
    ]
