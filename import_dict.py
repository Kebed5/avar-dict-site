import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "avar_dict_site.settings")
django.setup()

from dictapp.models import Entry
import pandas as pd
from django.db.utils import IntegrityError

df = pd.read_csv("Avar_Russian_Dict.csv")

for index, row in df.iterrows():
    try:
        Entry.objects.create(
            avar_word=row["avar_word"],
            russian_translations=row["russian_translations"],
            english_translations=row["english_translations"],
            examples=row.get("examples", "")
        )
    except IntegrityError:
        print(f"⚠️ Skipped duplicate: {row['avar_word']}")
