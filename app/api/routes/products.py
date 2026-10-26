from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import asc, desc, func, select
from sqlalchemy.orm import Session

from app.api.schemas import ProductListResponse, ProductResponse
from app.core.database import get_db
from app.models.product import Product

router = APIRouter(prefix="/api/v1/products", tags=["Products"])


@router.get("", response_model=ProductListResponse)
def list_products(
    category: str | None = Query(None, description="Filter by category"),
    min_price: float | None = Query(None, ge=0, description="Minimum price filter"),
    max_price: float | None = Query(None, ge=0, description="Maximum price filter"),
    material: str | None = Query(None, description="Filter by material"),
    colour: str | None = Query(None, description="Filter by colour"),
    style: str | None = Query(None, description="Filter by style"),
    availability: bool | None = Query(None, description="Filter by availability"),
    search: str | None = Query(None, description="Simple substring search"),
    sort_by: str = Query(
        "newest", description="Sort order: newest, price_asc, price_desc, title_asc"
    ),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(12, ge=1, le=50, description="Items per page"),
    db: Session = Depends(get_db),
):
    query = select(Product)

    if category:
        query = query.where(func.lower(Product.category) == category.lower())
    if min_price is not None:
        query = query.where(Product.price >= min_price)
    if max_price is not None:
        query = query.where(Product.price <= max_price)
    if material:
        query = query.where(func.lower(Product.material).contains(material.lower()))
    if colour:
        query = query.where(func.lower(Product.colour).contains(colour.lower()))
    if style:
        query = query.where(func.lower(Product.style).contains(style.lower()))
    if availability is not None:
        query = query.where(Product.availability == availability)
    if search:
        term = f"%{search.lower()}%"
        query = query.where(
            func.lower(Product.title).like(term)
            | func.lower(Product.description).like(term)
            | func.lower(Product.category).like(term)
        )

    # Count total matching
    count_stmt = select(func.count()).select_from(query.subquery())
    total = db.execute(count_stmt).scalar() or 0

    # Sorting
    if sort_by == "price_asc":
        query = query.order_by(asc(Product.price))
    elif sort_by == "price_desc":
        query = query.order_by(desc(Product.price))
    elif sort_by == "title_asc":
        query = query.order_by(asc(Product.title))
    else:  # newest
        query = query.order_by(desc(Product.created_at))

    # Pagination
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)

    items = db.execute(query).scalars().all()
    item_responses = [ProductResponse.model_validate(p) for p in items]

    return ProductListResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=item_responses,
    )


@router.get("/{product_id}", response_model=ProductResponse)
def get_product(product_id: str, db: Session = Depends(get_db)):
    product = db.execute(
        select(Product).where(Product.product_id == product_id.upper())
    ).scalar_one_or_none()
    if not product:
        raise HTTPException(
            status_code=404, detail=f"Product with ID '{product_id}' not found."
        )
    return ProductResponse.model_validate(product)
