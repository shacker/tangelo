# Tangelo - A Django-based image gallery built on the Flickr API

Rather than uploading images to your gallery site, site owners simple enter Flickr image IDs. Tangelo then pulls in and stores the full API response. After that, everything is built from that from that stored response.

For additional performance, the raw image data is stored in redis cache, for fastest possible image display.

A working example can be viewed at [shacker.net](https://shacker.net)

A demo video of the core concepts can be viewed [here](https://www.youtube.com/watch?v=K5676XDifrs)

*This is a gallery system for Python coders who also happen to be Flickr users, not for the
general public.* If you want a gallery system that doesn’t require writing or maintaining code, or if you are not familiar with Django, this project is not for you (try WordPress, or  quareSpace, or Lightroom Portfolios instead).

Anyone is free to help themselves to this source code, or even to make pull requests, but I will not support users who are learning Django or trying to deploy their first Django website.

## Installation
This repo represents a full Django project, not a reusable app. As a result, it is not pip
installable. Clone this repo and deploy it from a git checkout using your deployment system of
choice.

Set up is the usual - configure your database and media/static paths, `pip install -r requirements.txt`, etc.

This project is a bit unusual in having no local.py - instead use local.yml for localhost, and put
secrets in environment variables in your deployed server (env vars are read into settings via Goodconf).

## Settings
Get a Flickr key and secret [here](https://www.flickr.com/services/api/misc.api_keys.html). Then, in your project settings (env vars):

```
FLICKR_API_KEY: "123abc"
FLICKR_API_SECRET: "abc123"
FLICKR_USERNAME: "yourusername"

# See table on this page for image size reference:
# https://www.flickr.com/services/api/misc.urls.html
# b = 1024 on the long side
# h = 1024 on the long side
# n = 320px on the long side
FLICKR_IMAGE_SIZE: "h"
FLICKR_THUMBNAIL_SIZE: "n"
FLICKR_CROPPED_THUMB_SIZE: "q"
```

As always, keep secrets out of version control!

### Changing/Updating Python Dependencies

This project uses [pip-tools](https://pypi.org/project/pip-tools/) and its `pip-compile` to generate hashes for dependency installation. To add or update deps:

```
# Full:
pip-compile --generate-hashes --output-file=requirements.txt base.in

# Single package
pip-compile --generate-hashes --output-file=requirements.txt -P django-jsoneditor base.in
```

### Difference between flush_cache and refetch

Superuser will have a few links at the bottom of each image:

- Edit: Links to Django Admin edit view for this image
- Refetch: Reaches out to Flickr and overwrites our locally stored API data for this image
- Flush cache: Leave our db alone, but erases the cached redis data for this image so it's
  displayed with updates on next page load.

### Known Issues

- Image model has an `album_order` field that was initially meant for controlling the order of images as they appear in an album. But I had an issue with the drag/drop util I was using to make that easy, so I switched to date-based ordering. The old method is still half-there. Could be a user option in the future.

