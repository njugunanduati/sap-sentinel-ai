from app.services.error_codes import ErrorCode
from app.services.master_data import (
    SUPPORTED_CURRENCIES,
    VALID_MATERIALS,
    VALID_STORES
)


def detect_errors(event) -> list[dict]:

    errors = []

    if event.store_id not in VALID_STORES:
        errors.append({
            "code": ErrorCode.INVALID_STORE,
            "message": (
                f"Store {event.store_id} "
                "was not found in store master data."
            )
        })

    if not event.material_id:
        errors.append({
            "code": ErrorCode.MISSING_MATERIAL,
            "message": "Material identifier is missing."
        })

    elif event.material_id not in VALID_MATERIALS:
        errors.append({
            "code": ErrorCode.MISSING_MASTER_DATA,
            "message": (
                f"Material {event.material_id} "
                "was not found in material master data."
            )
        })

    if event.currency not in SUPPORTED_CURRENCIES:
        errors.append({
            "code": ErrorCode.INVALID_CURRENCY,
            "message": (
                f"Currency {event.currency} "
                "is not supported by this interface."
            )
        })

    return errors