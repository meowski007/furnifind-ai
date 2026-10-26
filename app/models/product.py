from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, Float, Index, String, Text

from app.core.database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Product(Base):
    __tablename__ = "products"

    product_id = Column(String(64), primary_key=True, index=True)
    title = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=False)
    category = Column(String(64), nullable=False, index=True)
    price = Column(Float, nullable=False, index=True)
    currency = Column(String(8), nullable=False, default="INR")
    material = Column(String(64), nullable=True, index=True)
    colour = Column(String(64), nullable=True, index=True)
    style = Column(String(64), nullable=True, index=True)
    width = Column(Float, nullable=True, index=True)  # in cm
    height = Column(Float, nullable=True)  # in cm
    depth = Column(Float, nullable=True)  # in cm
    image_path = Column(String(512), nullable=True)
    image_url = Column(String(1024), nullable=True)
    availability = Column(Boolean, nullable=False, default=True, index=True)
    source = Column(String(128), nullable=False, default="furnifind_catalogue")
    created_at = Column(DateTime, default=utc_now, nullable=False)

    __table_args__ = (
        Index("ix_products_cat_price", "category", "price"),
        Index("ix_products_style_cat", "style", "category"),
    )

    def to_dict(self):
        return {
            "product_id": self.product_id,
            "title": self.title,
            "description": self.description,
            "category": self.category,
            "price": self.price,
            "currency": self.currency,
            "material": self.material,
            "colour": self.colour,
            "style": self.style,
            "width": self.width,
            "height": self.height,
            "depth": self.depth,
            "image_path": self.image_path,
            "image_url": self.image_url,
            "availability": self.availability,
            "source": self.source,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
