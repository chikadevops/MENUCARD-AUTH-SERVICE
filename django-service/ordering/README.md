
---

### Setup Instructions

1. **Clone the repository**
   
   First, clone the repository to your local machine:

   git clone https://github.com/hngprojects/Menucard-App-Team-D-Backend.git
   cd Menucard-App-Team-D-Backend/django-service

2. **Create and activate a virtual environment**

   It's a good practice to use a virtual environment to keep dependencies isolated. Run the following commands to create and activate the virtual environment:

   python3 -m venv .venv
   source .venv/bin/activate   # For Linux/Mac
   .venv\Scripts\activate      # For Windows
 

3. **Install the required dependencies**

   Install the necessary Python dependencies listed in `requirements.txt`:

   pip install -r requirements.txt
 

4. **Set up environment variables**

   Make sure you have the necessary environment variables set up. Create a `.env` file in the root directory (if not already created) and add:

   
   DEBUG=True
   SECRET_KEY=your-secret-key
   ALLOWED_HOSTS=127.0.0.1,localhost
   DB_NAME=your_db_name
   DB_USER=your_db_user
   DB_PASSWORD=your_db_password
   DB_HOST=localhost
   DB_PORT=5432
   

   Adjust the values above as needed for your setup (e.g., your database credentials).

5. **Run migrations**

   Apply the migrations to set up the database schema:

  
   python manage.py migrate
   

6. **Create a superuser (optional)**

   If you need an admin user to access the Django admin panel, you can create one with the following command:

  
   python manage.py createsuperuser
  

   Follow the prompts to set up the admin user.

7. **Start the development server**

   Finally, run the development server:


   python manage.py runserver
 

   You should see the server running at `http://127.0.0.1:8000/`.

---

### API Base URL

- The base URL for the API is: `http://127.0.0.1:8000/api/`
- For example, to get the list of products, you would visit: `http://127.0.0.1:8000/api/products/`

---

### Authentication

- The order-related endpoints require **token authentication**.
- To authenticate, pass the token in the `Authorization` header for requests:

  
   Authorization: Token <your_token>

   You can retrieve the token by logging in or through any other token-based authentication mechanism in place.

---


### 🔐 Authentication
All order-related endpoints require token authentication.

Include this in your headers:
Authorization: Token <your_token>

---

### 📦 Products
**GET** `/api/products/`  
Returns a list of available products.

**GET** `/api/products/<id>/`  
Returns a single product

**GET** `/api/products/featured/`  
Returns featured items.

**GET** `/api/products/by_category/?category=1`  
Returns Products by category ID

---

### 🧾 Orders
**GET** `/api/orders/`  
List orders (authentication required).

**POST** `/api/orders/`  
Create a new order (authentication required).

**GET** `/api/order-items/<id>/`  
View order details

#### Order Items
- `PATCH /api/order-items/<id>/` - Update order item


Payload:
```json
{
  "items": [
    {"product": 1, "quantity": 2},
    {"product": 3, "quantity": 1}
  ]
}
