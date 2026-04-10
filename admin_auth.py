import config  # type: ignore

class AdminAuth:
    def __init__(self):
        self.pin = config.ADMIN_PIN

    def verify_pin(self, input_pin):
        return input_pin == self.pin

    def change_pin(self, old_pin, new_pin):
        if self.verify_pin(old_pin):
            self.pin = new_pin
            # In a real app, update config.py or a database
            return True
        return False
