from bunnet import Document

class BankConnection(Document):
    id: str
    bank_name: str

    class Settings:
        name = "bank_connections"

    @classmethod
    def new(cls, id, bank_name):
        return cls(id=id, bank_name=bank_name).save()