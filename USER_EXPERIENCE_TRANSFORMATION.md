# User Experience Transformation Plan

## Objective
Transform the entire user panel into a fully functional, real-time, and professionally themed experience.

## Status: IN PROGRESS

---

## ✅ Completed

### 1. Dashboard (`user/dashboard.html`)
- ✅ Removed all dummy data
- ✅ Integrated real-time stats from `/api/user/dashboard-stats`
- ✅ Integrated recent queries from `/api/user/recent-queries`
- ✅ Updated navigation with AI Chat and History links
- ✅ Modern dark/gold theme applied
- ✅ All icons updated to Font Awesome 6

### 2. Profile Page (`profile.html`)
- ✅ Fixed all `strftime` errors (dates now handled as strings)
- ✅ Updated route to fetch real-time user stats
- ✅ Displays actual query count, feedback, and satisfaction rate
- ✅ Shows recent activity from database
- ✅ Functional edit profile button (calls JavaScript)

### 3. Template Error Fixes
- ✅ Fixed `user/dashboard.html` - strftime on line 1362
- ✅ Fixed `profile.html` - strftime on lines 520, 524, 604
- ✅ Fixed `chat_history.html` - strftime on line 269

---

## 🔄 In Progress

### Backend API Endpoints
- ✅ `/api/user/dashboard-stats` - Real-time user statistics
- ✅ `/api/user/recent-queries` - Recent AI chat queries
- ⏳ `/api/user/consultations` - Need to make fully functional
- ⏳ `/api/messages` - Need real conversation system
- ⏳ `/api/documents` - Need real file upload/storage
- ⏳ `/api/search/cas` - Already real-time, needs UI integration

---

## 📋 Pending Transformations

### 4. Consultations Page (`user/consultations.html`)
**Status:** Template exists (35KB)
**Needed:**
- [ ] Remove dummy consultations
- [ ] Connect to real CA profiles
- [ ] Implement "New Consultation" button functionality
- [ ] Add filter tabs (All, Active, Waiting, Completed)
- [ ] Progress timeline with real status updates
- [ ] Chat with CA button integration
- [ ] Document sharing functionality

### 5. Messages Page (`user/messages.html`)
**Status:** Template exists (30KB)
**Needed:**
- [ ] Remove mock conversations
- [ ] Real-time message system
- [ ] Send message functionality
- [ ] Conversation search
- [ ] Online/offline status indicators
- [ ] Message attachments
- [ ] Encryption notice display

### 6. Documents Page (`user/documents.html`)
**Status:** Template exists (46KB)
**Needed:**
- [ ] File upload functionality
- [ ] Supabase Storage integration
- [ ] Folder organization (Tax, GST, Bank, Identity)
- [ ] Document preview
- [ ] Download functionality
- [ ] Share with CA feature
- [ ] Recent documents section with real data

### 7. Find CA Page (`user/find_ca.html`)
**Status:** Template exists (38KB)
**Needed:**
- [ ] Connect to `/api/search/cas` endpoint (already live)
- [ ] Working search filters (location, service, experience)
- [ ] Sort by dropdown functionality
- [ ] CA profile cards with real data
- [ ] "Request Consultation" button
- [ ] Rating and review display
- [ ] Service badges from CA profile

### 8. Settings Page (`user/settings.html`)
**Status:** Template exists (36KB)
**Needed:**
- [ ] Profile edit form with save functionality
- [ ] Password change form
- [ ] Email notification toggles (save to database)
- [ ] Privacy settings
- [ ] Two-factor authentication setup
- [ ] Account deletion option

---

## 🎨 Theme Consistency Requirements

All pages must follow this design system:

### Colors
```css
--primary-gold: #fba002 / #D4AF37
--dark-gold: #e69200 / #B8941F
--bg-dark: #0a0a0a / #1a1a1a
--bg-card: #151515 / #2a2a2a
--text-light: #ffffff
--text-muted: #999999 / #b0b0b0
--border: #2a2a2a / #404040
--success: #22c55e
--error: #ef4444
```

### Typography
- Font: Inter, system-ui, sans-serif
- Headings: 600-700 weight
- Body: 400-500 weight

### Components
- Sidebar: Dark background with gold accent on active
- Cards: Rounded corners (12-20px), subtle shadows
- Buttons: Gold primary, dark secondary
- Icons: Font Awesome 6 (consistent sizing)
- Stats: Large numbers in gold, labels in muted text

---

## 🔧 Functional Requirements

### All Pages Must Have:
1. **Real-time data** - No hardcoded/dummy values
2. **Loading states** - Spinners while fetching
3. **Empty states** - Friendly messages when no data
4. **Error handling** - Graceful fallbacks
5. **Responsive design** - Mobile-friendly
6. **Accessibility** - Proper ARIA labels
7. **Performance** - Fast load times

### All Buttons Must:
1. Have clear hover states
2. Show loading indicator when clicked
3. Execute actual backend operations
4. Provide user feedback (success/error messages)
5. Be disabled when operation in progress

---

## 📊 Database Requirements

### Tables Needed (Future Enhancement)
- `consultations` - Track CA-user consultations
- `messages` - Store chat messages
- `documents` - File metadata (actual files in Supabase Storage)
- `notifications` - User notifications
- `user_settings` - Preferences and toggles

---

## 🚀 Implementation Priority

1. **High Priority** (Immediate UX Impact)
   - Fix remaining strftime errors ✅
   - Profile page real-time stats ✅
   - Find CA search functionality
   - Consultations display

2. **Medium Priority** (Core Features)
   - Messages system
   - Documents upload/download
   - Settings form submissions

3. **Low Priority** (Nice to Have)
   - Advanced filters
   - Notifications system
   - Analytics dashboard

---

## 📝 Notes

- All API endpoints should return JSON with `{success: true/false, data: {...}, error: "..."}`
- Use JavaScript `fetch()` for all API calls
- Add proper CSRF protection for forms
- Implement rate limiting on sensitive endpoints
- Log all errors to console with descriptive messages

---

**Last Updated:** January 20, 2026
**Status:** Active Development
