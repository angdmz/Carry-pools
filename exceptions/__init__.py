from .general import ResourceNotFound, UnprocessableEntity, resource_not_found_handler, generic_unprocessable_entity_handler

handlers = {
    ResourceNotFound: resource_not_found_handler,
    UnprocessableEntity: generic_unprocessable_entity_handler,
}


def install_handlers_into_app(app):
    for k, v in handlers.items():
        app.add_exception_handler(k, v)
