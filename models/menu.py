from pydantic import BaseModel, Field


class Piatto(BaseModel):
    nome: str = Field(..., description="Nome del piatto")
    categoria: str = Field(
        ..., description="Categoria del piatto: Primo, Secondo, Antipasto, Dessert"
    )
    descrizione: str | None = Field(
        description="Descrizione del piatto o null", default=None
    )
    prezzo: float = Field(..., description="Prezzo del piatto")
    image_url: str | None = Field(
        description="URL dell'immagine del piatto", default=None
    )


class Bevanda(BaseModel):
    nome: str = Field(..., description="Nome della bevanda")
    descrizione: str | None = Field(
        description="Descrizione della bevanda o null", default=None
    )
    prezzo: float = Field(..., description="Prezzo della bevanda")


class Menu(BaseModel):
    piatti: list[Piatto] = Field(..., description="Lista dei piatti del menu")
    bevande: list[Bevanda] = Field(..., description="Lista delle bevande del menu")
    prezzo_coperto: float | None = Field(
        default=None, description="Prezzo del coperto o null"
    )
