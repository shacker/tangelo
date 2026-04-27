from django import forms

from gallery.models import Album


class ContactForm(forms.Form):
    your_email = forms.EmailField(required=True)
    subject = forms.CharField(required=True)
    message = forms.CharField(widget=forms.Textarea, required=True)


class AddImageForm(forms.Form):
    flickr_url = forms.CharField(
        label="Flickr URL or ID",
        help_text="Paste a full Flickr photo URL or just the numeric photo ID",
    )
    album = forms.ModelChoiceField(queryset=Album.objects.all().order_by("title"))
