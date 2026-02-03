# 👨‍💼 Admin Guide: Verify CA Applications

Complete step-by-step guide for admins to review and verify Chartered Accountant applications.

---

## 🚀 Quick Start

### Step 1: Become Admin (One-Time Setup)

**Option A: Using Supabase SQL (Recommended)**
1. Go to https://supabase.com → Your Project → SQL Editor
2. Run this SQL (replace with your email):

```sql
UPDATE profiles 
SET role = 'admin' 
WHERE email = 'your-email@example.com';
```

3. Logout and login again to refresh your session

**Option B: Using Supabase Table Editor**
1. Go to Supabase → Table Editor → `profiles`
2. Find your user by email
3. Change `role` column from `user` to `admin`
4. Save and logout/login

---

## 📋 Admin Dashboard Access

### Access Admin Panel
```
http://localhost:3000/admin/dashboard
```

Or click **"Admin Dashboard"** in the top navigation when logged in as admin.

---

## ✅ Review CA Applications Workflow

### Step 1: Access CA Applications
1. Go to Admin Dashboard
2. Click **"CA Applications"** in the navigation
3. You'll see all pending applications

### Step 2: Review Application Details
Each application shows:
- **Applicant Name** & Contact Info
- **ICAI Registration Number**
- **Experience & Specializations**
- **Practice Address**
- **Submitted Documents**
- **Application Status**

### Step 3: Verify Documents

#### What to Check:
1. **ICAI Certificate**
   - Valid ICAI registration number (format: ABC123456)
   - Certificate is not expired
   - Name matches application

2. **PAN Card**
   - Clear and readable
   - Name matches
   - Valid PAN format

3. **Aadhaar Card** (Optional)
   - Masked for privacy
   - For identity verification

4. **Practice Certificate**
   - Valid practice address
   - Current year certificate
   - Firm registration (if applicable)

5. **Professional Photo**
   - Clear headshot
   - Professional appearance

### Step 4: Take Action

#### ✅ To Approve Application:
1. Click **"Approve"** button on the application card
2. Optionally add admin notes (e.g., "All documents verified")
3. Confirm approval
4. The CA will be notified and can access CA Dashboard

#### ❌ To Reject Application:
1. Click **"Reject"** button
2. **Must provide rejection reason** (required)
3. Options:
   - Invalid ICAI number
   - Incomplete documents
   - Unverified credentials
   - Suspicious activity
   - Custom reason
4. The applicant will receive an email with the reason

#### ⏸️ To Request More Information:
1. Click **"Request Info"** button
2. Specify what additional information/documents are needed
3. Application status changes to "more_info_required"
4. Applicant can resubmit with requested docs

---

## 🔍 Application Statuses

| Status | Meaning | Action Required |
|--------|---------|-----------------|
| **pending** | New application submitted | Review & verify |
| **under_review** | Admin is reviewing | Continue review |
| **approved** | CA verified & active | None |
| **rejected** | Application denied | None (can reapply) |
| **more_info_required** | Needs additional docs | Wait for resubmission |

---

## 🛠️ Admin API Endpoints

Use these endpoints for custom admin tools:

### Get All Applications
```javascript
GET /api/ca-ecosystem/applications
GET /api/ca-ecosystem/applications?status=pending
```

### Get Single Application
```javascript
GET /api/ca-ecosystem/applications/{application_id}
```

### Approve Application
```javascript
POST /api/ca-ecosystem/applications/{application_id}/approve
Body: { "notes": "All documents verified" }
```

### Reject Application
```javascript
POST /api/ca-ecosystem/applications/{application_id}/reject
Body: { "reason": "Invalid ICAI number" }
```

### Request More Info
```javascript
POST /api/ca-ecosystem/applications/{application_id}/request-info
Body: { "message": "Please provide current year practice certificate" }
```

---

## 🎯 Best Practices

### Document Verification Checklist

**Before Approving, Ensure:**
- [ ] ICAI number is valid (check on ICAI website if needed)
- [ ] All required documents are uploaded
- [ ] Documents are clear and readable
- [ ] Name consistency across all documents
- [ ] Practice address is complete and valid
- [ ] Email and phone number are active
- [ ] No duplicate applications from same person
- [ ] No suspicious or fraudulent activity

### Response Time
- Review applications within **48 hours**
- Priority to complete applications with all docs
- Flag urgent cases that need faster review

### Communication
- Always provide clear reasons for rejection
- Be professional and courteous
- Offer guidance for reapplication
- Document all decisions in admin notes

---

## 📊 Admin Statistics

View key metrics on the dashboard:
- **Total Applications**: All time submissions
- **Pending Review**: Awaiting verification
- **Approved CAs**: Active verified CAs
- **Rejection Rate**: Quality control metric
- **Average Review Time**: Efficiency metric

---

## 🔒 Security Features

### Built-in Protection:
- ✅ Admin-only access to verification endpoints
- ✅ Rate limiting (max 20 approvals/rejections per minute)
- ✅ Audit logging (all actions tracked)
- ✅ IP tracking for suspicious activity
- ✅ Row Level Security in database

### Audit Trail:
All admin actions are logged:
- Who performed the action
- What action was taken
- When it happened
- Target application ID
- Reason/notes provided

---

## 🆘 Troubleshooting

### "Access Denied" Error
**Problem:** Can't access admin panel  
**Solution:** 
1. Verify role is 'admin' in database
2. Logout and login again
3. Clear browser cache/cookies

### No Applications Showing
**Problem:** Applications list is empty  
**Solution:**
1. Check if any applications submitted (user portal)
2. Verify database table exists (`ca_applications`)
3. Check browser console for errors

### Can't Approve/Reject
**Problem:** Buttons not working  
**Solution:**
1. Check if you're logged in as admin
2. Verify application_id is valid
3. Check network tab in browser DevTools

### Documents Not Loading
**Problem:** Can't view uploaded documents  
**Solution:**
1. Check Supabase Storage bucket permissions
2. Verify documents were uploaded correctly
3. Check CORS settings in Supabase

---

## 📞 Admin Support Commands

### Check Admin Status (Python)
```python
# Run this in Python terminal
from finucity.database import UserService
user = UserService.get_by_email('your-email@example.com')
print(f"Role: {user.get('role')}")
print(f"Is Admin: {user.get('role') == 'admin'}")
```

### View Recent Applications (SQL)
```sql
SELECT full_name, email, icai_number, status, created_at 
FROM ca_applications 
ORDER BY created_at DESC 
LIMIT 10;
```

### Count by Status (SQL)
```sql
SELECT status, COUNT(*) as count 
FROM ca_applications 
GROUP BY status;
```

---

## ✨ Quick Tips

1. **Use Filters**: Filter by status (pending, approved, rejected)
2. **Bulk Actions**: Select multiple applications for batch processing
3. **Search**: Search by name, email, or ICAI number
4. **Export**: Download applications list as CSV for reports
5. **Notifications**: Enable email notifications for new applications

---

## 🎉 Success!

Once you approve a CA application:
1. ✅ User role changes from `user` to `ca`
2. ✅ CA can access CA Dashboard at `/ca/dashboard`
3. ✅ CA appears in public directory (Find a CA)
4. ✅ CA can start accepting client requests
5. ✅ Email notification sent to CA

---

## 📚 Related Documentation

- [Project Structure](PROJECT_STRUCTURE.md) - Complete app overview
- [Navigation Guide](NAVIGATION_GUIDE.md) - All dashboard links
- [Admin Setup Guide](ADMIN_SETUP_GUIDE.md) - Initial admin setup
- [Supabase Setup](SUPABASE_SETUP.md) - Database configuration

---

**Questions?** Check the logs or contact support!

**Current Admin Email:** Check your `.env` file for configured admin email
