# API Documentation

## Authentication System

### User Registration Flow

#### 1. Register User
**POST** `/register/`
```json
{
    "username": "testuser",
    "email": "test@example.com", 
    "full_name": "Test User",
    "user_type": "customer" // or "vip_customer", "vendor"
}
```

**Response:**
```json
{
    "message": "OTP sent to your email."
}
```

#### 2. Verify OTP
**POST** `/verify-otp/`
```json
{
    "email": "test@example.com",
    "otp": "123456"
}
```

**Response (Customer):**
```json
{
    "message": "OTP verified successfully. You can now set your password at: /set-password/{user_id}/"
}
```

**Response (VIP/Vendor):**
```json
{
    "message": "OTP verified successfully. Please wait for admin approval."
}
```

#### 3. Set Password
**POST** `/set-password/{user_id}/`
```json
{
    "password": "SecurePass123!",
    "confirm_password": "SecurePass123!"
}
```

#### 4. Login
**POST** `/login/`
```json
{
    "username": "testuser",
    "password": "SecurePass123!"
}
```

**Response:**
```json
{
    "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

### Admin Operations

#### Admin Dashboard - View Pending Users
**GET** `/admin-dashboard/`
Headers: `Authorization: Bearer {admin_token}`

**Response:**
```json
[
    {
        "id": "uuid",
        "username": "vendor1",
        "email": "vendor@example.com",
        "full_name": "Vendor Name",
        "user_type": "vendor",
        "created_at": "2025-01-01T00:00:00Z"
    }
]
```

#### Approve/Reject User
**POST** `/admin-dashboard/`
```json
{
    "id": "user_uuid",
    "action": "approve", // or "reject"
    "rejection_reason": "Optional reason if rejecting"
}
```

### Products

#### List Products (Public)
**GET** `/Products/list/`

**Response for Regular Customer:**
```json
[
    {
        "id": "uuid",
        "name": "Product 1",
        "vendor": "vendor_id",
        "vendor_name": "Vendor Name",
        "retail_price": "100.00",
        "price": "100.00",
        "price_type": "retail",
        "stock_quantity": 50
    }
]
```

**Response for VIP Customer:**
```json
[
    {
        "id": "uuid", 
        "name": "Product 1",
        "vendor": "vendor_id",
        "vendor_name": "Vendor Name",
        "retail_price": "100.00",
        "whole_sale_price": "80.00",
        "price": "80.00",
        "price_type": "wholesale",
        "stock_quantity": 50
    }
]
```

#### Vendor Product Management

##### Get Vendor's Products
**GET** `/Products/vendor/`
Headers: `Authorization: Bearer {vendor_token}`

**Response:**
```json
[
    {
        "id": "uuid",
        "name": "My Product",
        "vendor": "vendor_profile_id",
        "vendor_name": "My Vendor Name",
        "retail_price": "100.00",
        "whole_sale_price": "80.00",
        "stock_quantity": 50
    }
]
```

##### Create Product
**POST** `/Products/vendor/`
Headers: `Authorization: Bearer {vendor_token}`

**Request:**
```json
{
    "name": "New Product",
    "retail_price": "150.00",
    "whole_sale_price": "120.00",
    "stock_quantity": 25
}
```

**Validation Rules:**
- Wholesale price must be less than retail price
- Stock quantity cannot be negative
- Name is required

##### Get Specific Product
**GET** `/Products/vendor/{product_id}/`
Headers: `Authorization: Bearer {vendor_token}`

##### Update Product
**PUT** `/Products/vendor/{product_id}/`
Headers: `Authorization: Bearer {vendor_token}`

**Request:**
```json
{
    "name": "Updated Product Name",
    "retail_price": "160.00",
    "whole_sale_price": "130.00",
    "stock_quantity": 30
}
```

##### Delete Product
**DELETE** `/Products/vendor/{product_id}/`
Headers: `Authorization: Bearer {vendor_token}`

**Response:**
```json
{
    "message": "Product deleted successfully"
}
```

## User Types & Access Levels

1. **Customer**: 
   - Auto-approved after email verification
   - Can set password immediately after OTP verification
   - Sees retail prices only

2. **VIP Customer**:
   - Requires admin approval after verification
   - Sees wholesale prices
   - Can purchase at wholesale rates

3. **Vendor**:
   - Requires admin approval after verification
   - Can see all pricing information
   - Can create, read, update, and delete their own products
   - Has full product management capabilities

## Password Requirements
- At least 8 characters
- At least one uppercase letter
- At least one lowercase letter  
- At least one digit
- At least one special character

## Vendor Workflow

1. **Registration**: Register as vendor
2. **Verification**: Verify email with OTP
3. **Admin Approval**: Wait for admin to approve account
4. **Password Setup**: Set password after approval
5. **Login**: Login with credentials
6. **Product Management**: Create and manage products

### Vendor Product Management Workflow

1. **View Products**: `GET /Products/vendor/` - See all your products
2. **Add Product**: `POST /Products/vendor/` - Create new product
3. **Edit Product**: `PUT /Products/vendor/{id}/` - Update existing product
4. **Delete Product**: `DELETE /Products/vendor/{id}/` - Remove product

## Error Codes
- `400` - Bad Request (validation errors)
- `401` - Unauthorized (invalid credentials)
- `403` - Forbidden (not approved, account locked, or insufficient permissions)
- `404` - Not Found (user/resource not found)
