# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

Tangelo is a Django image gallery backed by the Flickr API. Images are not uploaded directly — users
enter Flickr IDs, and the app fetches and caches full API metadata. Cached data lives in Redis with a
1-year TTL; dev uses DummyCache instead.

## Common Commands

This project uses `uv` for dependency management. Dependencies are declared in `pyproject.toml`;
`uv.lock` is the lockfile.

```bash
uv sync                          # install/sync all deps
uv add <package>                 # add a dependency
uv remove <package>              # remove a dependency
uv lock --upgrade                # update all deps
uv lock --upgrade-package django # update one dep

uv run python manage.py runserver
uv run python manage.py migrate
uv run python manage.py collectstatic
uv run python manage.py nuclear              # clear all caches
uv run python manage.py nuclear --refetch    # clear caches + re-pull all Flickr data
uv run python manage.py test gallery
uv run python manage.py test gallery.tests.ClassName.test_method
```

Code quality (no config files; use defaults):
```bash
uv run black .
uv run flake8 .
```

## Architecture

**One Django app:** `gallery/` handles everything — models, views, admin, templatetags, forms,
context processors, and management commands.

**Models** (`gallery/models.py`): All inherit from `django_extensions.TimeStampedModel`.
- `Album` — slug, title, about (markdown), display order, thumbnail FK to Image
- `Image` — Flickr ID, `image_api_data` JSONField (raw API response), title, taken date, album FK
- `SimplePage` — slug, title, body (markdown) for static pages like About

**Flickr Integration:** `Image.save()` auto-fetches full API metadata from Flickr on first save and
stores it in `image_api_data`. `get_embed_url()` constructs image URLs from stored server/ID/secret
fields. Three configurable sizes: detail, thumbnail, cropped thumbnail.

**Caching:** Template fragment caching for `flickr_full`, `flickr_thumb`, `album_thumb`. Cache flush
methods on `Image` model; admin actions for selective clearing. `nuclear` management command for bulk
operations.

**Context processor** (`gallery/context_processors.py`): Injects all albums into every template
context for navigation.

**Templatetags** (`gallery/templatetags/`): `album_thumb` and `image_thumb` are inclusion tags used
in gallery grids.

## Configuration

Uses `goodconf` — settings load from `tangelo/config/local.yml` in dev, env vars in production.
Config class is in `tangelo/config/config.py`; settings module is `tangelo/config/settings.py`.

Key env/config vars: `DATABASE_URL`, `REDIS_URL`, `FLICKR_API_KEY`, `FLICKR_API_SECRET`,
`FLICKR_IMAGE_SIZE`, `FLICKR_THUMBNAIL_SIZE`, `FLICKR_CROPPED_THUMB_SIZE`.

## URL Structure

```
/               home (album grid)
/a/<slug>       album detail
/i/<flickr_id>  image detail
/p/<slug>       simple page (about, etc.)
/contact/       contact form
/flush_cache/<flickr_id>   superuser only
/refetch/<flickr_id>       superuser only
/tadmin/        Django admin
```

## Dependencies

- `flickrapi` — Flickr API access
- `goodconf` — YAML + env var config management
- `django-extensions` — TimeStampedModel, shell_plus
<!-- - `adminsortable2` — drag-drop ordering in admin -->
- `jsoneditor` — visual editing of raw API JSON in Image admin
- `markdownify` — markdown rendering in templates
- `crispy-forms` (Bootstrap 4) — contact form
- `django-light` — forces light mode in Django admin
- `fabric` — deployment automation
- `dj-database-url` — parses `DATABASE_URL`
