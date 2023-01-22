class KivyStyles:
    style_callbacks=None

    def __init__(self):
        self.style_callbacks = dict()

    def register_callback(self, caller, key, callback):
        if key not in self.style_callbacks:
            self.style_callbacks[key]=dict()

        self.style_callbacks[key][caller]=callback

    def notify_style_change(self, key):
        if key not in self.style_callbacks:
            return

        for caller in self.style_callbacks[key].keys():
            callback=self.style_callbacks[key][caller]
            callback(key)