import os
import django
import pandas as pd


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "avar_dict_site.settings")
django.setup()

from dictapp.models import Entry
from django.db.utils import IntegrityError

# Read your CSV (no header)
df = pd.read_csv(
    "Avar_Russian_Dictionary_Structured.csv",
    sep=";",
    header=None,
    names=["AVAR", "RUSSIAN", "ENGLISH"]
)

for index, row in df.iterrows():
    try:
        Entry.objects.create(
            avar_word=row["AVAR"],
            russian_translations=row["RUSSIAN"],
            english_translations=row.get("ENGLISH", ""),
            examples=""
        )
    except IntegrityError:
        print(f"⚠️ Skipped duplicate: {row['AVAR']}")


