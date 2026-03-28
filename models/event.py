"""Event model – thin data class."""


class Event:
    def __init__(self, id, name, date, club):
        self.id = id
        self.name = name
        self.date = date
        self.club = club

    def __repr__(self):
        return f"<Event id={self.id} name={self.name!r}>"
