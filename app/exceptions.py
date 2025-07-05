from app import error_codes

async def validation_exception_handler(request, exc):
    errors = jsonable_encoder(exc.errors())
    if not errors:
        return JSONResponse(status_code=204, content=None)
    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "error": {
                "code": error_codes.VALIDATION_ERROR,
                "message": "Request validation failed.",
                "details": errors
            }
        },
    )
