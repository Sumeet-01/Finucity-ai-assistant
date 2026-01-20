# 🔐 Finucity Admin Setup Guide

## ✅ App is Ready to Run!

The duplicate endpoint error has been fixed. Your app should now start successfully.

---

## 🚀 Quick Start: Run Your App

```bash
python app.py
```

The app will start on `http://localhost:3000`

---

## 👨‍💼 How to Become Admin

### **Method 1: Direct SQL Update (Recommended)**

1. **Go to Supabase SQL Editor:**
   - Open https://supabase.com/dashboard
   - Select your project
   - Click **SQL Editor**

2. **Run this SQL to make yourself admin:**

```sql
-- Replace 'your-email@example.com' with your actual email
UPDATE profiles 
SET role = 'admin' 
WHERE email = 'your-email@example.com';
```

3. **Verify:**
```sql
SELECT email, role FROM profiles WHERE role = 'admin';
```

### **Method 2: After First Signup**

1. **Sign up normally** at `/register` or `/auth/login`
2. **Go to Supabase Table Editor**
3. **Find your user** in `profiles` table
4. **Edit the `role` column** to `admin`
5. **Logout and login again**

---

## 🎯 Admin Access

Once you're an admin, you can access:

### **Admin Dashboard**
```
http://localhost:3000/admin/dashboard
```

### **Manage Users**
```
http://localhost:3000/admin/users
```

### **CA Applications (Verify CAs)**
```
http://localhost:3000/admin/ca-applications
```

---

## 🔧 How to Make Others Admin

### **Option 1: Via Supabase SQL**

```sql
-- Make specific user admin
UPDATE profiles 
SET role = 'admin' 
WHERE email = 'newadmin@example.com';

-- Or by user ID
UPDATE profiles 
SET role = 'admin' 
WHERE id = 'user-uuid-here';
```

### **Option 2: Via API (When logged in as admin)**

```javascript
// Make a POST request
fetch('/api/admin/users/USER_ID_HERE/role', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    role: 'admin'  // or 'ca', 'user', 'ca_pending'
  })
});
```

---

## 📋 User Role Types

| Role | Description | Access |
|------|-------------|--------|
| **user** | Regular user | User dashboard, chat, find CA |
| **ca** | Verified CA | CA dashboard, client management |
| **ca_pending** | Pending CA verification | Limited access, waiting for admin approval |
| **admin** | Platform admin | Full access, user management, CA verification |

---

## 🎨 Admin Features

### **1. User Management**
- View all users
- Update user roles
- See user stats

### **2. CA Verification**
- View CA applications
- Approve/Reject CAs
- Manage CA status

### **3. Platform Stats**
- Total users
- Active CAs
- Pending applications
- Revenue metrics

---

## 🔐 Role-Based Routing

After login, users are automatically redirected based on their role:

```
admin      → /admin/dashboard
ca         → /ca/dashboard
ca_pending → /auth/ca-pending
user       → /user/dashboard
```

---

## 💡 API Endpoints for Admin

### **Get All Users**
```
GET /api/admin/users
```

### **Update User Role**
```
POST /api/admin/users/<user_id>/role
Body: { "role": "admin" }
```

### **Get Admin Stats**
```
GET /api/admin/stats
```

### **Get CA Applications**
```
GET /api/admin/ca-applications
```

### **Approve CA Application**
```
POST /api/admin/ca-application/<app_id>/approve
```

### **Reject CA Application**
```
POST /api/admin/ca-application/<app_id>/reject
Body: { "reason": "Rejection reason" }
```

---

## ✨ Complete User Flow

### **New User Signup:**
1. User visits `/auth/login`
2. Creates account (role: `user`)
3. Redirected to `/user/dashboard`

### **CA Application:**
1. User selects "CA" during signup/login
2. Redirected to `/auth/ca-apply`
3. Submits CA application
4. Role changed to `ca_pending`
5. Waits for admin approval

### **Admin Approval:**
1. Admin logs in → `/admin/dashboard`
2. Goes to `/admin/ca-applications`
3. Reviews application
4. Approves → CA role changed to `ca`
5. CA can now access `/ca/dashboard`

---

## 🧪 Testing Checklist

- [ ] App starts without errors
- [ ] Can sign up new user
- [ ] Can login with existing user
- [ ] User redirected to correct dashboard based on role
- [ ] Admin can access `/admin/dashboard`
- [ ] Admin can view all users
- [ ] Admin can update user roles
- [ ] Role changes reflected immediately after re-login

---

## 🆘 Troubleshooting

### **"Access Denied" when accessing admin routes**
- Check your role in Supabase: `SELECT role FROM profiles WHERE email = 'your-email'`
- Make sure it's exactly `'admin'` (lowercase)
- Logout and login again

### **Can't see admin menu**
- Verify `check_admin_access()` returns true
- Check browser console for errors
- Clear browser cache

### **User role not updating**
- After SQL update, logout and login again
- Check Flask session is cleared
- Verify Supabase profiles table updated

---

## 📝 Example: Complete Admin Setup

```sql
-- 1. Create your admin account (run in Supabase SQL Editor)
UPDATE profiles 
SET role = 'admin' 
WHERE email = 'admin@finucity.com';

-- 2. Verify
SELECT id, email, username, role FROM profiles WHERE role = 'admin';

-- 3. Make another user CA
UPDATE profiles 
SET role = 'ca' 
WHERE email = 'ca@finucity.com';

-- 4. Check all roles
SELECT email, role, created_at FROM profiles ORDER BY created_at DESC;
```

---

## 🎉 You're All Set!

Your admin system is fully functional. Run the app and start managing users!

```bash
python app.py
# Visit http://localhost:3000
# Login with your admin account
# Go to http://localhost:3000/admin/dashboard
```

**Happy Administrating! 🚀**
