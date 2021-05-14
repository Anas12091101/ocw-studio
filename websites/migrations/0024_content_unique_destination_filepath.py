# Generated by Django 3.1.6 on 2021-05-13 17:52
from collections import defaultdict

from django.db import migrations, models


def _config_item_folder_map(raw_site_config: dict) -> dict:
    collections = raw_site_config["collections"]
    return {
        config_item["name"]: config_item["folder"]
        for config_item in collections
        if "folder" in config_item
    }


def backpopulate_null_dirpaths(apps, schema_editor):
    """
    Finds all WebsiteContent records with a null dirpath, and sets the dirpath to the value in the site config if
    the content was created for a "folder"-type config item
    """
    WebsiteContent = apps.get_model("websites", "WebsiteContent")
    WebsiteStarter = apps.get_model("websites", "WebsiteStarter")

    starter_qset = WebsiteStarter.objects.values("id", "config")
    config_folder_map = {
        starter_dict["id"]: _config_item_folder_map(starter_dict["config"])
        for starter_dict in starter_qset
    }
    content_qset = WebsiteContent.objects.filter(dirpath=None).values(
        "id", "type", "website__starter_id"
    )
    starter_type_map = defaultdict(lambda: defaultdict(list))
    for content_dict in content_qset:
        starter_id = content_dict["website__starter_id"]
        content_type = content_dict["type"]
        if content_type in config_folder_map[starter_id]:
            starter_type_map[starter_id][content_type].append(content_dict["id"])

    for starter_id, type_id_map in starter_type_map.items():
        for content_type, content_ids in type_id_map.items():
            WebsiteContent.objects.filter(id__in=content_ids).update(
                dirpath=config_folder_map[starter_id][content_type],
                is_page_content=True,
            )


class Migration(migrations.Migration):

    dependencies = [
        ("websites", "0023_website_content_filepath"),
    ]

    operations = [
        migrations.RunPython(backpopulate_null_dirpaths, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="websitecontent",
            name="dirpath",
            field=models.CharField(
                default="",
                help_text="The directory path for the file that will be created from this object.",
                max_length=300,
            ),
        ),
        migrations.AlterField(
            model_name="websitecontent",
            name="filename",
            field=models.CharField(
                default="",
                help_text="The filename of the file that will be created from this object WITHOUT the file extension.",
                max_length=125,
            ),
        ),
        migrations.AlterUniqueTogether(
            name="websitecontent",
            unique_together=set(),
        ),
        migrations.AddConstraint(
            model_name="websitecontent",
            constraint=models.UniqueConstraint(
                fields=("website", "text_id"), name="unique_text_id"
            ),
        ),
        migrations.AddConstraint(
            model_name="websitecontent",
            constraint=models.UniqueConstraint(
                condition=models.Q(is_page_content=True),
                fields=("website", "dirpath", "filename"),
                name="unique_page_content_destination",
            ),
        ),
    ]
