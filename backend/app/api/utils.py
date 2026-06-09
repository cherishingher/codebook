from decimal import Decimal


def public_model(item, fields: list[str]) -> dict:
    data = {}
    for field in fields:
        value = getattr(item, field)
        if isinstance(value, Decimal):
            value = float(value)
        data[field] = value
    return data


def page_response(items: list, *, page: int, page_size: int, total: int | None = None) -> dict:
    return {
        "items": items,
        "page": page,
        "page_size": page_size,
        "total": total if total is not None else len(items),
    }
