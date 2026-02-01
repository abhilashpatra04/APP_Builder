from datetime import date

class TodoItem:
    def __init__(self, id: int, title: str, description: str, due_date: date):
        self.id = id
        self.title = title
        self.description = description
        self.due_date = due_date