def http_response(code, body):
    return {"statusCode": code, "body": body}


def response(code, body):
    return http_response(code, body)


def response_error(code, body):
    return http_response(code, body)
