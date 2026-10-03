# DrapeStudio Inventory

A simple inventory management app I built for my family's women's clothing shop — tracks sarees, suits, and other stock, lets staff log in securely, add new stock, adjust quantities as items sell, and quickly see what's running low.

This isn't a customer-facing store — it's an internal tool for managing inventory.

## What it does

- Staff can sign up and log in using JWT-based authentication
- Add new products with details like category, fabric, color, size, price, and starting quantity
- Quickly increase or decrease stock with +/- controls as items are sold or restocked (never goes below zero)
- View all products, or filter to just the ones running low on stock
- Delete discontinued items
- All inventory routes are protected — only logged-in users can view or modify stock

## Built with

### Backend
- Python + FastAPI
- PostgreSQL (Neon)
- SQLModel for the ORM
- python-jose for JWT
- passlib + bcrypt for password hashing
- slowapi for rate limiting on login
- Pydantic's EmailStr for email format validation

### Frontend
- React (Vite)
- React Router for page navigation (Login vs Dashboard)
- Axios, with an interceptor that automatically attaches the JWT token to every request

## API

| Method | Route | What it does |
|--------|-------|---------------|
| POST | `/signup` | create a new staff account |
| POST | `/login` | returns access + refresh tokens (rate limited: 5/min) |
| POST | `/refresh` | get a new access token using a refresh token |
| GET | `/me` | returns the logged-in user's info |
| POST | `/products` | add a new product |
| GET | `/products` | list all products (optional ?category= filter) |
| GET | `/products/low-stock` | list products below their stock threshold |
| GET | `/products/{id}` | get a single product |
| PUT | `/products/{id}` | update a product's details |
| PATCH | `/products/{id}/stock` | increase or decrease stock by a given amount |
| DELETE | `/products/{id}` | delete a product |

## Running it locally

**Backend:**
```bash
git clone https://github.com/Mani12568/drapestudio-inventory.git
cd drapestudio-inventory
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

Create a `.env` file:
```
DATABASE_URL=your_postgresql_connection_string
```

```bash
uvicorn main:app --reload
```

Backend runs on `http://127.0.0.1:8000`, docs at `/docs`.

**Frontend (new terminal):**
```bash
cd frontend
npm install
npm run dev
```

Frontend runs on `http://localhost:5173`.

## Notes

This project reuses the JWT authentication pattern from an earlier Auth Service project I built, since I already understood it deeply — signup, login, bcrypt password hashing, access and refresh tokens, and a protected-route pattern.

The one genuinely new feature here is the stock adjustment route (`PATCH /products/{id}/stock`) — instead of editing a product's full details just to record a sale, there's a dedicated endpoint that increases or decreases quantity by a given amount, with validation that stops stock from going negative.

I ran into the exact same passlib/bcrypt version compatibility bug I'd hit before on a different project, but recognized it immediately from the error signature and fixed it in under a minute. I also hit a new issue this time — a newer SQLModel version requiring timezone-aware datetimes instead of naive ones, which I hadn't seen before and had to debug fresh.

## What I'd improve with more time

- Role-based access (e.g., owner vs staff) instead of every logged-in user having full access
- Refresh token rotation
- Automated tests with pytest
- Deploy both frontend and backend live