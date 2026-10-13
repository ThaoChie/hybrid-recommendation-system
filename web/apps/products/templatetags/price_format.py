from django import template

register = template.Library()


@register.filter
def vnd(value):
    """Format giá tiền VND: 2300023 → 2.300.023"""
    try:
        num = int(float(value))
        return f"{num:,}".replace(",", ".")
    except (ValueError, TypeError):
        return value
