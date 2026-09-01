import re
import time

from django import forms
from django.core import signing

from gallery.models import Album

# Reject a submit that arrives faster than a human can type a message,
# or one whose form page is stale enough to be a replayed POST.
MIN_FILL_SECONDS = 3
MAX_FORM_AGE_SECONDS = 60 * 60 * 2

# Real messages to a photo site almost never carry more than one link.
MAX_LINKS = 1

LINK_RE = re.compile(r"https?://|www\.", re.IGNORECASE)


class ContactForm(forms.Form):
    your_email = forms.EmailField(required=True)
    subject = forms.CharField(required=True)
    message = forms.CharField(widget=forms.Textarea, required=True)

    # Honeypot. Hidden from humans by CSS in contact.html; bots fill it in.
    website = forms.CharField(
        required=False,
        label="Website",
        widget=forms.TextInput(attrs={"autocomplete": "off", "tabindex": "-1"}),
    )

    # Signed render time, used to measure how long the form took to fill in.
    timestamp = forms.CharField(required=False, widget=forms.HiddenInput())

    def __init__(self, *args, **kwargs) -> None:
        """Stamp each freshly rendered form with a signed render time."""
        super().__init__(*args, **kwargs)
        self.fields["timestamp"].initial = signing.dumps(time.time())

    def clean_website(self) -> str:
        """Fail if the honeypot field holds any value - only a bot fills it."""
        if self.cleaned_data.get("website"):
            raise forms.ValidationError("Submission rejected.")
        return ""

    def clean_timestamp(self) -> str:
        """Fail if the form was submitted too fast, too late, or unsigned."""
        raw = self.cleaned_data.get("timestamp", "")
        try:
            rendered_at = signing.loads(raw)
        except signing.BadSignature:
            raise forms.ValidationError("Submission rejected.")

        elapsed = time.time() - float(rendered_at)
        if elapsed < MIN_FILL_SECONDS or elapsed > MAX_FORM_AGE_SECONDS:
            raise forms.ValidationError("Submission rejected.")
        return raw

    def clean_message(self) -> str:
        """Fail if the message holds more links than a real message needs."""
        message = self.cleaned_data["message"]
        if len(LINK_RE.findall(message)) > MAX_LINKS:
            raise forms.ValidationError("Please remove the links from your message and try again.")
        return message


class AddImageForm(forms.Form):
    flickr_url = forms.CharField(
        label="Flickr URL or ID",
        help_text="Paste a full Flickr photo URL or just the numeric photo ID",
    )
    albums = forms.ModelMultipleChoiceField(
        queryset=Album.objects.all().order_by("title"),
        widget=forms.SelectMultiple(
            attrs={
                "class": "selectpicker",
                "data-live-search": "true",
                "data-style": "btn-outline-secondary",
                "title": "Select albums…",
            }
        ),
    )
