from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, EmailStr
from sqlmodel import Session, select
from datetime import datetime, timezone
from fastapi.middleware.cors import CORSMiddleware

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from database import engine, get_session
from models import User, Product, SQLModel
from auth import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


@app.on_event("startup")
def on_startup():
    SQLModel.metadata.create_all(engine)


# ---------- Request schemas ----------

class SignupRequest(BaseModel):
    email: EmailStr
    password: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class RefreshRequest(BaseModel):
    refresh_token: str

class ProductCreate(BaseModel):
    name: str
    category: str
    fabric: str | None = None
    color: str | None = None
    size: str | None = None
    price: float
    quantity: int = 0
    low_stock_threshold: int = 5

class ProductUpdate(BaseModel):
    name: str | None = None
    category: str | None = None
    fabric: str | None = None
    color: str | None = None
    size: str | None = None
    price: float | None = None
    quantity: int | None = None
    low_stock_threshold: int | None = None


# ---------- Auth helper ----------

def get_current_user(token: str = Depends(oauth2_scheme), session: Session = Depends(get_session)):
    payload = decode_token(token)
    if payload is None or payload.get("type") != "access":
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    email = payload.get("sub")
    user = session.exec(select(User).where(User.email == email)).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


# ---------- Auth routes ----------

@app.post("/signup")
def signup(body: SignupRequest, session: Session = Depends(get_session)):
    existing_user = session.exec(select(User).where(User.email == body.email)).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    new_user = User(email=body.email, hashed_password=hash_password(body.password))
    session.add(new_user)
    session.commit()
    session.refresh(new_user)
    return {"message": "User created successfully", "user_id": new_user.id}


@app.post("/login")
@limiter.limit("5/minute")
def login(request: Request, body: LoginRequest, session: Session = Depends(get_session)):
    user = session.exec(select(User).where(User.email == body.email)).first()
    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    access_token = create_access_token({"sub": user.email})
    refresh_token = create_refresh_token({"sub": user.email})
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}


@app.post("/refresh")
def refresh_access_token(body: RefreshRequest):
    payload = decode_token(body.refresh_token)
    if payload is None or payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")
    new_access_token = create_access_token({"sub": payload.get("sub")})
    return {"access_token": new_access_token, "token_type": "bearer"}


@app.get("/me")
def read_current_user(user: User = Depends(get_current_user)):
    return {"id": user.id, "email": user.email, "created_at": user.created_at}


# ---------- Product (inventory) routes — all protected ----------

@app.post("/products")
def create_product(body: ProductCreate, session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    product = Product(**body.dict())
    session.add(product)
    session.commit()
    session.refresh(product)
    return product


@app.get("/products")
def list_products(category: str | None = None, session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    query = select(Product)
    if category:
        query = query.where(Product.category == category)
    return session.exec(query).all()


@app.get("/products/low-stock")
def low_stock_products(session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    products = session.exec(select(Product)).all()
    return [p for p in products if p.quantity < p.low_stock_threshold]


@app.get("/products/{product_id}")
def get_product(product_id: int, session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    product = session.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@app.put("/products/{product_id}")
def update_product(product_id: int, body: ProductUpdate, session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    product = session.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    update_data = body.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(product, key, value)
    product.updated_at = datetime.now(timezone.utc)

    session.add(product)
    session.commit()
    session.refresh(product)
    return product


@app.delete("/products/{product_id}")
def delete_product(product_id: int, session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    product = session.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    session.delete(product)
    session.commit()
    return {"message": "Product deleted"}

class StockAdjust(BaseModel):
    change: int  # e.g. -1 to decrease, +1 to increase

@app.patch("/products/{product_id}/stock")
def adjust_stock(product_id: int, body: StockAdjust, session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    product = session.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    new_quantity = product.quantity + body.change
    if new_quantity < 0:
        raise HTTPException(status_code=400, detail="Stock cannot go below zero")

    product.quantity = new_quantity
    product.updated_at = datetime.now(timezone.utc)

    session.add(product)
    session.commit()
    session.refresh(product)
    return product