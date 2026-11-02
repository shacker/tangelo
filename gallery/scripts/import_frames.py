"""
One-off import of frame inventory from the Frames CSV (an export of the Google
Sheet) into Frame records. Run with django-extensions' runscript:

    uv run python manage.py runscript import_frames --script-args dry-run
    uv run python manage.py runscript import_frames
    uv run python manage.py runscript import_frames --script-args replace
    uv run python manage.py runscript import_frames --script-args path/to/other.csv dry-run

With no path, reads gallery/fixtures/Frames_110126.csv.

Options are bare words (runscript would swallow "--" flags):
    dry-run   Run the full import, report results, then roll back.
    replace   Delete all existing Frame records before importing.

Columns are matched by header name, not position; unknown columns (e.g. Mat Order)
are ignored. Everything runs in one transaction: any error rolls back the whole import.
"""

import csv
from decimal import Decimal
from pathlib import Path

from django.core.management.base import CommandError
from django.core.management.color import color_style
from django.db import transaction

from gallery.models import (
    Frame,
    FrameState,
    Image,
    Location,
    Price,
    generate_photo_id,
    nearest_aspect_ratio,
)

DEFAULT_CSV = Path(__file__).resolve().parent.parent / "fixtures" / "Frames_110126.csv"

OPTIONS = {"dry-run": "dry_run", "replace": "replace"}

# CSV header -> Frame field (text fields only; FKs/M2M/numbers handled separately)
TEXT_COLUMNS = {
    "Title": "title",
    "LR ID": "lr_id",
    "Frame": "frame",
    "Image dimension": "image_dimension",
    "Rabet size": "rabbet_size",
    "Notes": "notes",
    "Print order": "print_order",
}
REQUIRED_HEADERS = set(TEXT_COLUMNS) | {
    "TODO",
    "Aspect",
    "Price",
    "Photo ID",
    "State",
    "Print cost",
    "Location",
}
OPTIONAL_HEADERS = {"Flickr ID"}


class DryRun(Exception):
    pass


def to_text(value) -> str:
    """Normalize a cell to trimmed text."""
    return (value or "").strip()


class Importer:
    def __init__(self):
        self.style = color_style()

    def out(self, msg):
        print(msg)

    def handle(self, **opts):
        path = Path(opts["csv_path"])
        try:
            # utf-8-sig: tolerate the byte-order mark some spreadsheet exports add.
            with path.open(newline="", encoding="utf-8-sig") as f:
                rows = list(csv.reader(f))
        except OSError as e:
            raise CommandError(f"Could not open CSV: {e}")
        if not rows:
            raise CommandError(f"{path} is empty.")
        self.out(f"Reading {path}")

        if Frame.objects.exists() and not opts["replace"]:
            raise CommandError(
                f"{Frame.objects.count()} Frame records already exist. "
                'Add the "replace" script arg to delete them and re-import.'
            )

        self.created_lookups = []
        self.warnings = []

        try:
            with transaction.atomic():
                if opts["replace"]:
                    deleted = Frame.objects.all().delete()[1].get("gallery.Frame", 0)
                    self.out(f"Deleted {deleted} existing frames.")

                count = self.import_rows(rows)

                if opts["dry_run"]:
                    raise DryRun
        except DryRun:
            pass

        self.out(f'{count} frames {"checked" if opts["dry_run"] else "imported"}')
        for msg in self.created_lookups:
            self.out(self.style.WARNING(f"Created lookup: {msg}"))
        for msg in self.warnings:
            self.out(self.style.WARNING(msg))
        if opts["dry_run"]:
            self.out(self.style.NOTICE("Dry run: all changes rolled back."))
        else:
            self.out(self.style.SUCCESS(f"Done. {Frame.objects.count()} frames in database."))

    # ### Per-row ###

    def import_rows(self, rows: list) -> int:
        headers = [to_text(h) for h in rows[0]]
        missing = REQUIRED_HEADERS - set(headers)
        if missing:
            raise CommandError(f'CSV is missing columns: {", ".join(sorted(missing))}')
        col = {h: i for i, h in enumerate(headers) if h in REQUIRED_HEADERS | OPTIONAL_HEADERS}

        n = 0
        for rownum, row in enumerate(rows[1:], start=2):
            cell = {h: to_text(row[i]) if i < len(row) else "" for h, i in col.items()}
            if not any(v for h, v in cell.items() if h != "Photo ID"):
                continue  # blank row, or a placeholder row with only a Photo ID
            self.import_row(cell, f"Row {rownum}")
            n += 1
        return n

    def import_row(self, cell: dict, where: str):
        p = Frame()
        for header, field in TEXT_COLUMNS.items():
            setattr(p, field, to_text(cell[header]))
        todo = to_text(cell["TODO"])
        if todo:  # TODO text lives at the end of Notes
            p.notes = f"{p.notes}\n\nTODO: {todo}".strip()

        p.aspect = self.get_aspect(p, cell["Aspect"])
        p.price = self.get_price(cell["Price"], where)
        p.location = self.get_location(cell["Location"])  # blank -> None, not the "Home" default
        p.print_cost = self.get_cost(cell["Print cost"], where)
        p.photo_id = self.get_photo_id(p, cell["Photo ID"], where)
        p.image = self.get_image(p, cell.get("Flickr ID", ""), where)

        p.full_clean(exclude=["states"])
        p.save()
        p.states.set(self.get_states(cell["State"]))

    # ### Field converters ###

    def get_price(self, value, where):
        text = to_text(value)
        if not text or text.lower() == "unset":
            return None
        try:
            amount = int(Decimal(text.lstrip("$")))
        except Exception:
            raise CommandError(f'{where}: unrecognized Price "{text}"')
        price, created = Price.objects.get_or_create(amount=amount)
        if created:
            self.created_lookups.append(f"Price ${amount}")
        return price

    def get_aspect(self, p: Frame, value):
        """Snap to the nearest standard ratio; keep the original text in Notes if it differs.
        Frames with no Aspect get one computed from their dimensions when saved."""
        text = to_text(value)
        if not text:
            return None
        aspect = nearest_aspect_ratio(text)
        if aspect is None or aspect.name != text:
            p.notes = f"{p.notes}\n\nOriginal aspect: {text}".strip()
        p.aspect_manual = aspect is not None  # spreadsheet aspects were entered by hand
        return aspect

    def get_image(self, p: Frame, value, where):
        """Link the gallery Image with this Flickr ID, if it's in the gallery."""
        text = to_text(value)
        if not text:
            return None
        if not text.isdigit():
            raise CommandError(f'{where}: unrecognized Flickr ID "{text}"')
        image = Image.objects.filter(flickr_id=int(text)).first()
        if image is None:
            self.warnings.append(
                f'{where} "{p.title}": no gallery image with Flickr ID {text}; left unlinked.'
            )
        return image

    def get_location(self, value):
        name = to_text(value)
        if not name:
            return None
        loc = Location.objects.filter(name__iexact=name).first()
        if loc is None:
            loc = Location.objects.create(name=name)
            self.created_lookups.append(f'Location "{name}"')
        return loc

    def get_states(self, value):
        states = []
        for name in (s.strip() for s in to_text(value).split(",")):
            if not name:
                continue
            state = FrameState.objects.filter(name__iexact=name).first()
            if state is None:
                state = FrameState.objects.create(name=name, order=999)
                self.created_lookups.append(f'State "{name}"')
            states.append(state)
        return states

    def get_cost(self, value, where):
        text = to_text(value)
        if not text:
            return None
        try:
            return Decimal(text.lstrip("$")).quantize(Decimal("0.01"))
        except Exception:
            raise CommandError(f'{where}: unrecognized Print cost "{text}"')

    def get_photo_id(self, p: Frame, value, where) -> int:
        text = to_text(value)
        try:
            photo_id = int(text) if text else None
        except ValueError:
            raise CommandError(f'{where}: unrecognized Photo ID "{text}"')

        if photo_id is not None and not Frame.objects.filter(photo_id=photo_id).exists():
            return photo_id

        new_id = generate_photo_id()
        if photo_id is None:
            note = f"Photo ID {new_id} assigned on import (spreadsheet had none)."
        else:
            note = f"Photo ID changed from {photo_id} to {new_id} on import (duplicate)."
        p.notes = f"{p.notes}\n\n{note}".strip()
        self.warnings.append(f'{where} "{p.title}": {note}')
        return new_id


def run(*args):
    """Entry point for runscript. Returns an exit code (non-zero on failure)."""
    paths = [a for a in args if a not in OPTIONS]
    unknown = [a for a in args if a.startswith("-")]
    if len(paths) > 1 or unknown:
        print(__doc__)
        return 1
    opts = {field: (word in args) for word, field in OPTIONS.items()}
    try:
        Importer().handle(csv_path=paths[0] if paths else DEFAULT_CSV, **opts)
    except CommandError as e:
        print(color_style().ERROR(f"Error: {e}"))
        return 1
    return 0
