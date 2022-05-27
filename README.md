# Tangelo
A Django-based image gallery built on the Flickr API. A working example can be viewed at [shacker.net](https://shacker.net)

*This is a gallery system for Python coders who also happen to be Flickr*
*users, not for the general public.*

If you want a gallery system that doesn’t require writing or maintaining code,
or if you are not familiar with Django, this project is not for you (try WordPress, or SquareSpace, or Lightroom Portfolios instead).

Anyone is free to help themselves to this source code, or even to make pull requests, but I will not support users who are learning Django for the first time.

## Installation
This repo represents a full Django project, not a reusable app. As a result, it is not pip installable. Clone this repo and deploy it from a git check out using your deployment system of choice.

## Settings
Get a Flickr key and secret [here](https://www.flickr.com/services/api/misc.api_keys.html). Then, in your project settings:

```
FLICKR_API_KEY: "123abc"
FLICKR_API_SECRET: "abc123"
FLICKR_USERNAME: "yourusername"

# See table on this page for image size reference:
# https://www.flickr.com/services/api/misc.urls.html
# b = 1024 on the long side
# n = 320px on the long side
FLICKR_IMAGE_SIZE: "b"
FLICKR_THUMBNAIL_SIZE: "n"
```

As always, keep secrets out of version control! Your key should be in an environment variable.

### Changing Python Dependencies

This project uses [pip-tools](https://pypi.org/project/pip-tools/) and its pip-compile to generate hashes for dependency installation. To add or update deps:

```
# Full:
pip-compile --generate-hashes --output-file=requirements.txt base.in

# Single package
pip-compile --generate-hashes --output-file=requirements.txt -P dateutils base.in
```

### Difference between flush_cache and refetch

Superuser will have a few links at the bottom of each image:

- Admin: Links to Admin edit view for this image
- Refetch: Reaches out to Flickr and overwrites our locally stored db data for this image
- Flush cache: Leave our db alone, but erase the redis cached data for this image so it's regenerated on next load

### Known Issues

Realized late in the process that we prob don't need individual fields for title, description, date, etc. - we should store the whole JSON response in a JSONField and process it directly.
