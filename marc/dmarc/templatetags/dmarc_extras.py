import json
import re
from typing import Any

import markdown
from django import template
from django.utils.crypto import get_random_string
from django.utils.safestring import mark_safe

register = template.Library()
multi_spaces = re.compile(r"[ ]+")


@register.filter(name="jsonify")
def jsonify(value: Any) -> str:
    return mark_safe(json.dumps(value))


@register.filter(name="sum")
def _sum(value: list) -> Any:
    return sum(value)


@register.filter(name="class_help_text")
def class_help_text(value: Any) -> str:
    if not isinstance(value, type):
        value = type(value)

    raw = multi_spaces.sub(" ", value.__doc__.split("\n\n\n")[0])
    return mark_safe(markdown.markdown(raw))


@register.simple_tag(name="random_string")
def random_string(length: int = 8) -> str:
    return get_random_string(length=length)
