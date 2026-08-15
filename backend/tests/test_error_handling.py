def test_unknown_route_returns_404(client):
    response = client.get("/api/v1/this-route-does-not-exist")
    assert response.status_code == 404


def test_correlation_id_header_present_on_every_response(client):
    # RequestLoggingMiddleware must attach this even on error responses -
    # it's how a farmer-reported "something went wrong" gets traced to a
    # specific server-side log line without ever showing them a stack trace.
    response = client.get("/api/v1/health")
    assert "x-correlation-id" in response.headers

    error_response = client.get("/api/v1/this-route-does-not-exist")
    assert "x-correlation-id" in error_response.headers


# NOTE: a full test of register_exception_handlers' 500-path and the
# RequestValidationError JSON shape needs a real request-body endpoint to
# trigger against, which doesn't exist yet in this foundation phase (no
# fake business endpoints were created just to test the handler - see
# Step 11). Add those cases alongside the first real POST endpoint
# (/api/v1/auth/otp/request) in the next phase.
