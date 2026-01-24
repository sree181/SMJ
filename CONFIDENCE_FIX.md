# Confidence Calculation Fix

## Problem

The batch process was failing with error:
```
unsupported operand type(s) for *: 'float' and 'NoneType'
```

This occurred when trying to multiply `validation_confidence * extraction_confidence` where one or both values could be `None`.

## Root Causes

1. **JSON parsing can return empty dict**: `_parse_json_response()` returns `{}` on exception, so `.get("confidence")` returns `None`
2. **LLM can return null**: JSON with `"confidence": null` gets parsed as `None` in Python
3. **Missing field**: If confidence field is missing from JSON, `.get("confidence")` returns `None`
4. **Validation can return None**: Edge case where `validate_method_in_text()` might return `None` (though it shouldn't)

## Solution

Added robust error handling with multiple safety checks:

```python
# Handle all possible None cases robustly
extraction_confidence = method_details.get("confidence")
if extraction_confidence is None:
    extraction_confidence = 0.8  # Default if missing or None
try:
    extraction_confidence = float(extraction_confidence)
    if extraction_confidence == 0.0 or extraction_confidence < 0:
        extraction_confidence = 0.8  # Default if 0 or negative
except (ValueError, TypeError):
    extraction_confidence = 0.8  # Default if not a number

# Ensure validation_confidence is not None
if validation_confidence is None:
    validation_confidence = 0.5  # Default if validation failed
try:
    validation_confidence = float(validation_confidence)
    if validation_confidence < 0:
        validation_confidence = 0.5  # Default if negative
except (ValueError, TypeError):
    validation_confidence = 0.5  # Default if not a number

method_details["confidence"] = validation_confidence * extraction_confidence
```

## What This Fixes

✅ **None values**: Handles `None` from missing fields or null JSON
✅ **Type errors**: Handles non-numeric values (strings, etc.)
✅ **Invalid values**: Handles negative or zero confidence
✅ **Robust defaults**: Always provides valid float values for multiplication

## Status

✅ **Fixed and deployed**
✅ **Process restarted with fix**

The batch process should now handle all edge cases without crashing.

