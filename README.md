# Tangelo
A Django-based image gallery built on the Flickr API. Rather than uploading images to your gallery site, you can only enter Flickr image IDs. Tangelo then pulls in and stores (for performance) the full API response, and does everything subsequently from that stored response, including building image URLs.

For additional performance, the raw image data is stored in redis cache, for fastest possible image display.

A working example can be viewed at [shacker.net](https://shacker.net)

A demo video of the core concepts can be viewed [here](https://www.youtube.com/watch?v=Orn_mZ8quqE)

*This is a gallery system for Python coders who also happen to be Flickr users, not for the
general public.* If you want a gallery system that doesn’t require writing or maintaining code, or if you are not
familiar with Django, this project is not for you (try WordPress, or SquareSpace, or Lightroom
Portfolios instead).

Anyone is free to help themselves to this source code, or even to make pull requests, but I will not
support users who are learning Django for the first time.


## Installation
This repo represents a full Django project, not a reusable app. As a result, it is not pip
installable. Clone this repo and deploy it from a git checkout using your deployment system of
choice.

Set up is the usual - configure your database and media/static paths, `pip install -r requirements.txt`, etc.

This project is a bit unusual in having no local.py - instead use local.yml for localhost, and put
secrets in environment variables in your deployed server.


## Settings
Get a Flickr key and secret [here](https://www.flickr.com/services/api/misc.api_keys.html). Then, in
your project settings (env vars):

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

This project uses [pip-tools](https://pypi.org/project/pip-tools/) and its pip-compile to generate
hashes for dependency installation. To add or update deps:

```
# Full:
pip-compile --generate-hashes --output-file=requirements.txt base.in

# Single package
pip-compile --generate-hashes --output-file=requirements.txt -P django-jsoneditor base.in
```

### Difference between flush_cache and refetch

Superuser will have a few links at the bottom of each image:

- Admin: Links to Admin edit view for this image
- Refetch: Reaches out to Flickr and overwrites our locally stored db data for this image
- Flush cache: Leave our db alone, but erase the redis cached data for this image so it's
  regenerated on next load

### Known Issues

- Image has an album_order field that was initially meant for controlling the order of images as
they appear in an album. But I had an issue with the drag/drop util I was using to make that easy,
switch to date- based ordering, and decided I liked that better. The old method is still half-there
- could be a user option in the future.

