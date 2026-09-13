import os
import random
import requests
import uuid
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

API_URL = f'{os.getenv("API_URL")}interfaces/events'

stores = [
    "STORE-101",
    "STORE-102",
    "STORE-103",
    "STORE-104",
    "STORE-105"
]


materials = [
    "MAT-10001",
    "MAT-10002",
    "MAT-10003",
    "MAT-10004",
    "MAT-10005"
]


def generate_event():

    system_quantity = random.randint(10, 200)

    # Most inventory counts should be reasonably close
    physical_quantity = system_quantity + random.randint(-10, 10)

    physical_quantity = max(
        physical_quantity,
        0
    )

    return {
        "interface_id": "S4-POS-INVENTORY",

        "event_id": (
            f"EVT-{uuid.uuid4().hex[:8].upper()}"
        ),

        "store_id": random.choice(stores),

        "material_id": random.choice(materials),

        "movement_type": "PHYSICAL_INVENTORY",

        "system_quantity": system_quantity,

        "physical_quantity": physical_quantity,

        "unit_price": round(
            random.uniform(2.99, 150.00),
            2
        ),

        "currency": "USD",

        "timestamp": datetime.now().isoformat()
    }


for _ in range(50):

    event = generate_event()
    print("event: ", event)

    response = requests.post(
        API_URL,
        json=event
    )

    print(
        event["event_id"],
        response.status_code
    )