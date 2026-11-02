"""
Spreadsheet-style grid for editing Frame inventory at /frames/.

The page loads every frame as JSON and renders it with Tabulator. Each cell
edit POSTs a single field to frame_update, which validates it through a
one-field ModelForm (so model validation, unique checks, and M2M saving all
behave exactly as in the admin) and returns the saved row.
"""

import json
from functools import wraps

from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.forms import modelform_factory
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from gallery.models import AspectRatio, Frame, FrameState, FrameType, Image, Location, Price

# Fields the grid may edit. Anything else posted is rejected.
EDITABLE_FIELDS = [
    "title",
    "lr_id",
    "photo_id",
    "image",
    "price",
    "states",
    "location",
    "frame",
    "image_dimension",
    "rabbet_size",
    "aspect",
    "notes",
    "print_cost",
    "print_order",
    "frame_type",
]


def superuser_required(view):
    """Superusers only. Logged-out page requests redirect to the admin login so you can
    sign in; everyone else (any POST, or a signed-in non-superuser) gets a 403."""

    @wraps(view)
    def wrapped(request, *args, **kwargs):
        if request.user.is_superuser:
            return view(request, *args, **kwargs)
        if request.method == "POST":
            return JsonResponse({"error": "Not authorized."}, status=403)
        if request.user.is_authenticated:
            raise PermissionDenied
        return redirect_to_login(request.get_full_path(), login_url=reverse("admin:login"))

    return wrapped


def lookup_options(qs) -> list:
    """Dropdown options for a lookup model, with the tag color for the grid."""
    return [{"value": o.pk, "label": str(o), "color": o.color} for o in qs]


def image_label(img: Image) -> str:
    return f"{img.title or 'Untitled'} ({img.flickr_id})"


def serialize_frame(p: Frame) -> dict:
    return {
        "id": p.pk,
        "title": p.title,
        "lr_id": p.lr_id,
        "photo_id": p.photo_id,
        "image": p.image_id,
        "image_label": image_label(p.image) if p.image else "",
        "price": p.price_id,
        "states": [s.pk for s in p.states.all()],
        "location": p.location_id,
        "frame": p.frame,
        "image_dimension": p.image_dimension,
        "rabbet_size": p.rabbet_size,
        "aspect": p.aspect_id,
        "aspect_manual": p.aspect_manual,
        "notes": p.notes,
        "print_cost": str(p.print_cost) if p.print_cost is not None else None,
        "print_order": p.print_order,
        "frame_type": p.frame_type_id,
        "admin_url": reverse("admin:gallery_frame_change", args=[p.pk]),
    }


@superuser_required
def frames_grid(request):
    frames = (
        Frame.objects.select_related("image", "aspect")
        .prefetch_related("states")
        .order_by("title", "photo_id")
    )
    grid_data = {
        "rows": [serialize_frame(p) for p in frames],
        "prices": lookup_options(Price.objects.all()),
        "locations": lookup_options(Location.objects.all()),
        "frame_types": lookup_options(FrameType.objects.all()),
        "states": lookup_options(FrameState.objects.all()),
        "aspects": lookup_options(AspectRatio.objects.all()),
        "urls": {
            "update": reverse("frame_update", args=[0]),  # JS swaps in the real pk
            "add": reverse("frame_add"),
            "image_search": reverse("frame_image_search"),
        },
    }
    return render(request, "frames_grid.html", {"grid_data": grid_data})


@require_POST
@superuser_required
def frame_update(request, pk: int):
    """Update one field of one Frame. Body: {"field": "...", "value": ...}"""
    p = get_object_or_404(Frame, pk=pk)
    try:
        payload = json.loads(request.body)
        field = payload["field"]
        value = payload.get("value")
    except (ValueError, KeyError, TypeError):
        return JsonResponse({"error": "Malformed request."}, status=400)

    if field not in EDITABLE_FIELDS:
        return JsonResponse({"error": f'Field "{field}" is not editable.'}, status=400)

    if value is None:
        value = [] if field == "states" else ""
    if isinstance(value, str):
        value = value.strip()

    form_class = modelform_factory(Frame, fields=[field])
    form = form_class(data={field: value}, instance=p)
    if not form.is_valid():
        errors = "; ".join(e for errs in form.errors.values() for e in errs)
        if field == "image" and "image" in form.errors:
            errors = "That gallery image no longer exists."
        # The form has already written the bad value onto p; send back the stored row.
        stored = Frame.objects.select_related("image").prefetch_related("states").get(pk=pk)
        return JsonResponse({"error": errors, "row": serialize_frame(stored)}, status=400)

    if field == "aspect":
        # Picking an aspect overrides the computed one; "(none)" goes back to automatic.
        form.instance.aspect_manual = form.cleaned_data["aspect"] is not None
    form.save()
    p.refresh_from_db()
    return JsonResponse({"row": serialize_frame(p)})


@require_POST
@superuser_required
def frame_add(request):
    """Create a blank Frame using model defaults (auto Photo ID, Home location)."""
    p = Frame.objects.create()
    return JsonResponse({"row": serialize_frame(p)})


@superuser_required
def frame_image_search(request):
    """Autocomplete source for the grid's Image column: ?q= matches title or Flickr ID."""
    q = request.GET.get("q", "").strip()
    images = Image.objects.all()
    if q:
        match = Q(title__icontains=q)
        if q.isdigit():
            match |= Q(flickr_id__startswith=q)
        images = images.filter(match)
    images = images.order_by("title")[:25]
    return JsonResponse({"results": [{"value": i.pk, "label": image_label(i)} for i in images]})
