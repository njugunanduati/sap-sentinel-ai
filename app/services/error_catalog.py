from app.services.error_codes import ErrorCode, Severity


ERROR_CATALOG = {

    ErrorCode.INVALID_CURRENCY: {
        "severity": Severity.MEDIUM,
        "error_type": "VALIDATION_ERROR",
        "description": "Unsupported currency received."
    },

    ErrorCode.INVALID_STORE: {
        "severity": Severity.HIGH,
        "error_type": "MASTER_DATA_ERROR",
        "description": "Store could not be identified."
    },

    ErrorCode.MISSING_MATERIAL: {
        "severity": Severity.HIGH,
        "error_type": "VALIDATION_ERROR",
        "description": "Material identifier is missing."
    },

    ErrorCode.MISSING_MASTER_DATA: {
        "severity": Severity.HIGH,
        "error_type": "MASTER_DATA_ERROR",
        "description": "Required material master data was not found."
    },

    ErrorCode.QUANTITY_VALIDATION_ERROR: {
        "severity": Severity.MEDIUM,
        "error_type": "VALIDATION_ERROR",
        "description": "Inventory quantity failed validation."
    },

    ErrorCode.DUPLICATE_TRANSACTION: {
        "severity": Severity.HIGH,
        "error_type": "DUPLICATE_ERROR",
        "description": "Transaction has already been processed."
    },

    ErrorCode.MAPPING_ERROR: {
        "severity": Severity.HIGH,
        "error_type": "MAPPING_ERROR",
        "description": "Source data could not be mapped to the target format."
    },

    ErrorCode.INTERFACE_TIMEOUT: {
        "severity": Severity.CRITICAL,
        "error_type": "CONNECTIVITY_ERROR",
        "description": "Communication with downstream interface timed out."
    }
}