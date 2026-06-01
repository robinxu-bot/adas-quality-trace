"""Read-only common model tables — seeded from data/ JSON, never written at runtime."""
import sqlalchemy as sa
from sqlalchemy import String, Integer, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from app.models.enums import QualityAspect, ProductLine, ApplicabilityValue


class CommonCharacteristic(Base):
    __tablename__ = "common_characteristics"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    display_order: Mapped[int] = mapped_column(Integer, default=0)

    subcharacteristics: Mapped[list["CommonSubcharacteristic"]] = relationship(
        back_populates="characteristic", order_by="CommonSubcharacteristic.display_order"
    )


class CommonSubcharacteristic(Base):
    __tablename__ = "common_subcharacteristics"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    characteristic_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("common_characteristics.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    architecture_element: Mapped[str | None] = mapped_column(String(128))
    display_order: Mapped[int] = mapped_column(Integer, default=0)

    characteristic: Mapped[CommonCharacteristic] = relationship(
        back_populates="subcharacteristics"
    )
    aspect_mappings: Mapped[list["CommonAspectMapping"]] = relationship(
        back_populates="subcharacteristic"
    )
    product_line_recommendations: Mapped[list["ProductLineRecommendation"]] = relationship(
        back_populates="subcharacteristic"
    )


class CommonAspectMapping(Base):
    __tablename__ = "common_aspect_mappings"

    subchar_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("common_subcharacteristics.id"), primary_key=True
    )
    aspect: Mapped[QualityAspect] = mapped_column(
        sa.String(64), primary_key=True
    )

    subcharacteristic: Mapped[CommonSubcharacteristic] = relationship(
        back_populates="aspect_mappings"
    )


class ProductLineRecommendation(Base):
    __tablename__ = "product_line_recommendations"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    product_line: Mapped[ProductLine] = mapped_column(sa.String(64), nullable=False)
    subchar_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("common_subcharacteristics.id"), nullable=False
    )
    recommended_applicability: Mapped[ApplicabilityValue] = mapped_column(
        sa.String(64), nullable=False
    )
    default_rationale: Mapped[str | None] = mapped_column(Text)

    subcharacteristic: Mapped[CommonSubcharacteristic] = relationship(
        back_populates="product_line_recommendations"
    )
    recommended_aspects: Mapped[list["ProductLineRecommendationAspect"]] = relationship(
        back_populates="recommendation", cascade="all, delete-orphan"
    )


class ProductLineRecommendationAspect(Base):
    __tablename__ = "product_line_recommendation_aspects"

    recommendation_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("product_line_recommendations.id"), primary_key=True
    )
    aspect: Mapped[QualityAspect] = mapped_column(
        sa.String(64), primary_key=True
    )

    recommendation: Mapped[ProductLineRecommendation] = relationship(
        back_populates="recommended_aspects"
    )
