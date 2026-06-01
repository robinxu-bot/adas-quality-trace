from pydantic import BaseModel


class SubcharacteristicOut(BaseModel):
    id: str
    name: str
    description: str | None = None
    applicable_aspects: list[str] = []
    architecture_element: str | None = None

    model_config = {"from_attributes": True}


class CharacteristicOut(BaseModel):
    id: str
    name: str
    description: str | None = None
    subcharacteristics: list[SubcharacteristicOut] = []

    model_config = {"from_attributes": True}


class CommonModelOut(BaseModel):
    characteristics: list[CharacteristicOut]


class ProductLineRecommendationOut(BaseModel):
    subchar_id: str
    recommended_applicability: str
    recommended_aspects: list[str]
    default_rationale: str | None = None

    model_config = {"from_attributes": True}
