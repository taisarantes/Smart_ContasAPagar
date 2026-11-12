from pydantic import BaseModel

class RespostaConciliacao(BaseModel):

    resultado: str

    fonte: list[str]

    suficiente: bool

    justificativa: str