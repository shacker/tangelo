import time

from django.core import mail, signing
from django.test import TestCase
from django.urls import reverse

from gallery.forms import ContactForm


def valid_post(**overrides) -> dict:
    """Build a contact POST that passes every spam check unless overridden."""
    data = {
        "your_email": "someone@example.com",
        "subject": "Hello",
        "message": "I like your photos.",
        "website": "",
        "timestamp": signing.dumps(time.time() - 10),
    }
    data.update(overrides)
    return data


class ContactFormSpamTests(TestCase):
    """Cover the honeypot, timing, and link checks on the contact form."""

    def test_clean_submission_is_valid(self):
        """A normal, human-paced submission passes."""
        self.assertTrue(ContactForm(data=valid_post()).is_valid())

    def test_honeypot_rejects(self):
        """A filled honeypot field fails validation."""
        form = ContactForm(data=valid_post(website="http://spam.example"))
        self.assertFalse(form.is_valid())
        self.assertIn("website", form.errors)

    def test_too_fast_rejects(self):
        """A submission faster than a human can type fails validation."""
        form = ContactForm(data=valid_post(timestamp=signing.dumps(time.time())))
        self.assertFalse(form.is_valid())
        self.assertIn("timestamp", form.errors)

    def test_stale_form_rejects(self):
        """A form page older than the maximum age fails validation."""
        stale = signing.dumps(time.time() - (60 * 60 * 3))
        form = ContactForm(data=valid_post(timestamp=stale))
        self.assertFalse(form.is_valid())
        self.assertIn("timestamp", form.errors)

    def test_forged_timestamp_rejects(self):
        """An unsigned or tampered timestamp fails validation."""
        form = ContactForm(data=valid_post(timestamp="not-a-signed-value"))
        self.assertFalse(form.is_valid())
        self.assertIn("timestamp", form.errors)

    def test_many_links_rejects(self):
        """A message with more links than allowed fails validation."""
        message = "Buy http://a.example and http://b.example now"
        form = ContactForm(data=valid_post(message=message))
        self.assertFalse(form.is_valid())
        self.assertIn("message", form.errors)


class ContactViewSpamTests(TestCase):
    """Cover how the contact view answers bots and people."""

    def test_clean_submission_sends_mail(self):
        """A valid submission sends one message and shows the success page."""
        response = self.client.post(reverse("contact"), valid_post())
        self.assertRedirects(response, reverse("contact_success"))
        self.assertEqual(len(mail.outbox), 1)

    def test_trapped_submission_looks_successful_but_sends_nothing(self):
        """A tripped trap gets the success page and sends no mail."""
        data = valid_post(website="http://spam.example")
        response = self.client.post(reverse("contact"), data)
        self.assertRedirects(response, reverse("contact_success"))
        self.assertEqual(len(mail.outbox), 0)

    def test_link_heavy_submission_redisplays_form(self):
        """A link-heavy message returns the form with an error, not success."""
        data = valid_post(message="http://a.example http://b.example")
        response = self.client.post(reverse("contact"), data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(mail.outbox), 0)
