# app/schemas/currency.py

from pydantic import BaseModel


class DeviseResponse(BaseModel):
    code_devise: str
    nom: str
    symbole: str

    model_config = {"from_attributes": True}
