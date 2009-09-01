class IExternalAPI(object):
    def __init__(self):
        raise NotImplementedError
    def expose_method(self, name, callback, input_types, output_types):
        raise NotImplementedError
    def delete_method(self, name, callback):
        raise NotImplementedError
    def expose_event(self, name, output_types):
        raise NotImplementedError
    def emit_event(self, name, output_types):
        raise NotImplementedError


