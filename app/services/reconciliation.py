from decimal import Decimal

def reconcile_inventory(
        system_quantity: int,
        physical_quantity: int,
        unit_price: float
) -> dict:

    variance = physical_quantity - system_quantity

    financial_exposure = (
        abs(Decimal(str(variance)))
        * Decimal(str(unit_price))
    )

    if variance == 0:
        status = "MATCHED"

    elif abs(variance) <= 2:
        status = "MINOR_VARIANCE"

    else:
        status = "RECONCILIATION_REQUIRED"

    return {
        "system_quantity": system_quantity,
        "physcal_quantity": physical_quantity,
        "variance": variance,
        "financial_exposure": float(financial_exposure),
        "status": status
    }