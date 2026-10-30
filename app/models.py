from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class UserRegisterRequest(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=100)
    email: str = Field(..., min_length=5, max_length=120)
    password: str = Field(..., min_length=6, max_length=128)
    phone: Optional[str] = None

class UserLoginRequest(BaseModel):
    email: str
    password: str

class ProductCreateRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=200)
    slug: Optional[str] = None
    category_id: Optional[int] = None
    brand_id: Optional[int] = None
    sku: Optional[str] = None
    short_description: Optional[str] = None
    description: Optional[str] = None
    features: List[str] = []
    regular_price: int = Field(..., ge=0)
    sale_price: Optional[int] = Field(None, ge=0)
    is_featured: bool = False
    is_trending: bool = False
    status: str = "active"
    delivery_type: str = "license_key"
    delivery_instructions: Optional[str] = None
    seo_title: Optional[str] = None
    seo_description: Optional[str] = None
    sort_order: int = 0
    license_keys: Optional[List[str]] = []
    variants: Optional[List[Dict[str, Any]]] = []

class ProductUpdateRequest(BaseModel):
    name: Optional[str] = None
    slug: Optional[str] = None
    category_id: Optional[int] = None
    brand_id: Optional[int] = None
    sku: Optional[str] = None
    short_description: Optional[str] = None
    description: Optional[str] = None
    features: Optional[List[str]] = None
    regular_price: Optional[int] = None
    sale_price: Optional[int] = None
    is_featured: Optional[bool] = None
    is_trending: Optional[bool] = None
    status: Optional[str] = None
    delivery_type: Optional[str] = None
    delivery_instructions: Optional[str] = None
    seo_title: Optional[str] = None
    seo_description: Optional[str] = None
    sort_order: Optional[int] = None
    variants: Optional[List[Dict[str, Any]]] = None

class CategoryCreateRequest(BaseModel):
    name: str
    slug: Optional[str] = None
    description: Optional[str] = None
    icon: Optional[str] = "tag"
    display_order: int = 0
    is_active: bool = True

class BrandCreateRequest(BaseModel):
    name: str
    slug: Optional[str] = None
    logo_url: Optional[str] = None
    website: Optional[str] = None
    is_active: bool = True

class VoucherCreateRequest(BaseModel):
    code: str
    discount_type: str
    discount_value: int
    min_order_amount: int = 0
    max_discount: int = 0
    usage_limit: int = 0
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    is_active: bool = True

class ApplyVoucherRequest(BaseModel):
    code: str
    subtotal: int

class CartItemAddRequest(BaseModel):
    product_id: int
    variant_id: Optional[int] = None
    variant_name: Optional[str] = None
    quantity: int = 1

class CheckoutRequest(BaseModel):
    customer_name: str
    customer_email: str
    customer_phone: Optional[str] = None
    payment_method: str
    voucher_code: Optional[str] = None
    notes: Optional[str] = None

class StoreSettingsRequest(BaseModel):
    store_name: Optional[str] = None
    store_tagline: Optional[str] = None
    store_description: Optional[str] = None
    contact_email: Optional[str] = None
    contact_whatsapp: Optional[str] = None
    contact_address: Optional[str] = None
    hero_title: Optional[str] = None
    hero_subtitle: Optional[str] = None
    hero_badge: Optional[str] = None
    primary_color: Optional[str] = None
    dark_mode_default: Optional[str] = None
    maintenance_mode: Optional[str] = None
    currency_symbol: Optional[str] = None
    bank_name: Optional[str] = None
    bank_account_number: Optional[str] = None
    bank_account_holder: Optional[str] = None
    wa_order_enabled: Optional[str] = None
    wa_greeting_template: Optional[str] = None
