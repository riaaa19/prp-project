"""Registration model – thin data class."""


class Registration:
    def __init__(self, id, user_id, event_id):
        self.id = id
        self.user_id = user_id
        self.event_id = event_id

    def __repr__(self):
        return f"<Registration id={self.id} user={self.user_id} event={self.event_id}>"
