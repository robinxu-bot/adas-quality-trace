from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.common import (
    CommonCharacteristic, CommonSubcharacteristic,
    CommonAspectMapping, ProductLineRecommendation,
    ProductLineRecommendationAspect,
)
from app.models.enums import ProductLine
from app.schemas.common import (
    CommonModelOut, CharacteristicOut, SubcharacteristicOut,
    ProductLineRecommendationOut,
)

router = APIRouter(prefix="/common", tags=["common"])


@router.get("/model", response_model=CommonModelOut)
async def get_common_model(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(CommonCharacteristic)
        .options(
            selectinload(CommonCharacteristic.subcharacteristics)
            .selectinload(CommonSubcharacteristic.aspect_mappings)
        )
        .order_by(CommonCharacteristic.display_order)
    )
    characteristics = result.scalars().all()

    chars_out = []
    for char in characteristics:
        subs_out = []
        for sub in sorted(char.subcharacteristics, key=lambda s: s.display_order):
            aspects = [m.aspect for m in sub.aspect_mappings]
            subs_out.append(SubcharacteristicOut(
                id=sub.id,
                name=sub.name,
                description=sub.description,
                applicable_aspects=aspects,
                architecture_element=sub.architecture_element,
            ))
        chars_out.append(CharacteristicOut(
            id=char.id,
            name=char.name,
            description=char.description,
            subcharacteristics=subs_out,
        ))

    return CommonModelOut(characteristics=chars_out)


@router.get("/product-lines/{product_line}/recommendations",
            response_model=list[ProductLineRecommendationOut])
async def get_product_line_recommendations(
    product_line: str, db: AsyncSession = Depends(get_db)
):
    try:
        pl = ProductLine(product_line)
        pl_str = pl.value
    except ValueError:
        raise HTTPException(
            status_code=422,
            detail=f"Unknown product line '{product_line}'. "
                   f"Valid values: {[e.value for e in ProductLine]}"
        )

    result = await db.execute(
        select(ProductLineRecommendation)
        .options(selectinload(ProductLineRecommendation.recommended_aspects))
        .where(ProductLineRecommendation.product_line == pl_str)
    )
    recs = result.scalars().all()

    return [
        ProductLineRecommendationOut(
            subchar_id=r.subchar_id,
            recommended_applicability=r.recommended_applicability,
            recommended_aspects=[a.aspect for a in r.recommended_aspects],
            default_rationale=r.default_rationale,
        )
        for r in recs
    ]
