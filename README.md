# tangelo
Django-based image gallery built on the Flickr API

Keep your Flickr API credentials secret

### Changing Python Dependencies

To add, remove, or change the project's Python dependencies, edit `base.in` (global) or `dev.in`
(developer only). To "lock" your dependencies, run `make requirements.txt` or `make
requirements/dev.txt` or both. Because make is smart about these things, it will only do something
if the source files (base.in or dev.in) have changed. Note that this also means that updates to the
unversioned packages referenced in dev.in won't be picked up automatically! You can force it to
upgrade them with:

```
pip-compile --generate-hashes --output-file=requirements.txt base.in

# or, to just force it to update one package, do one of:

pip-compile --generate-hashes --output-file=requirements.txt -P package_name base.in
```

## Settings specific to this project

You'll need to establish these project settings.
Get a Flickr key and secret here:
https://www.flickr.com/services/api/misc.api_keys.html

```
FLICKR_API_KEY: "123abc"
FLICKR_API_SECRET: "abc123"
FLICKR_USERNAME: "yourusername"

# See table on this page for image size reference: https://www.flickr.com/services/api/misc.urls.html
# b = 1024 on the long side
# n = 320px on the long side
FLICKR_IMAGE_SIZE: "b"
FLICKR_THUMBNAIL_SIZE: "n"
```