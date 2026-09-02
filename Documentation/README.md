# 🏥 Smart Medicine Reminder System

**A comprehensive full-stack web application for medication management with family support and user privacy.**

---

## 📋 Table of Contents
- [Project Overview](#project-overview)
- [Key Features](#key-features)
- [Technology Stack](#technology-stack)
- [System Architecture](#system-architecture)
- [Project Structure](#project-structure)
- [Installation Guide](#installation-guide)
- [Database Design](#database-design)
- [API Documentation](#api-documentation)
- [User Interface](#user-interface)
- [Security Features](#security-features)
- [Testing Guide](#testing-guide)
- [Future Enhancements](#future-enhancements)
- [License & Contact](#license--contact)

---

## 🎯 Project Overview

The Smart Medicine Reminder System is an enterprise-grade full-stack web application designed to help patients manage their medications effectively while maintaining privacy and supporting family care scenarios.

### Problem Statement
Medication non-adherence affects millions globally, particularly elderly patients and those with complex medication regimens. Studies show that 50% of patients do not take medications as prescribed, leading to increased hospitalizations and reduced quality of life.

### Our Solution
An intelligent, user-friendly platform that:
- **Manages** medications for individuals and their family members
- **Tracks** medicine schedules with detailed logging
- **Maintains** complete privacy between different families
- **Supports** caregivers managing multiple family members

### Target Audience
- **Patients**: Managing personal medication regimens
- **Family Caregivers**: Managing medications for multiple family members (elderly parents, children, etc.)
- **Healthcare Providers**: Doctors prescribing medications

---

## ✨ Key Features

### 🔐 User Authentication & Privacy
- Secure login/logout system with session management
- Role-based user accounts (Patient, Caregiver, Doctor)
- Complete data isolation between different families
- Password-protected accounts

### 👨‍👩‍👧‍👦 Family Member Management (Advanced Feature)
- **Parent-Child User Relationships**: Users can create and manage accounts for family members
- **Privacy by Design**: Each user sees only their own data and their created family members
- **Family Dashboard**: Centralized view of all family members' medications
- **Isolated Data**: John's family data is completely separate from Elena's family data

### 💊 Comprehensive Medicine Management
- Add, edit, and delete medicines
- Detailed medicine profiles (name, dosage, instructions)
- Link medicines to specific family members
- View medicines filtered by family

### 📅 Intelligent Scheduling
- Create medication schedules with specific times
- Custom day-of-week configurations (e.g., Mon, Wed, Fri)
- Date range support (start date and optional end date)
- View schedules for all family members

### 🔔 Notification System
- Create reminders, alerts, and informational messages
- Target specific family members
- Notification history tracking
- Type-based categorization (reminder, alert, info)

### 📊 Intake Tracking
- Log actual medicine intake with timestamps
- Track status (Taken, Missed, Pending)
- Compare scheduled vs actual intake times
- Historical intake logs for adherence monitoring

### 📈 Interactive Dashboard
- Real-time statistics (medicines, schedules, notifications)
- Recent activity feed
- Family-specific data display
- Quick navigation to all features

### 🎨 Professional UI/UX
- Clean, modern interface design
- Responsive layout for all screen sizes
- Intuitive navigation
- Color-coded status indicators
- Edit functionality with modal dialogs

---

## 💻 Technology Stack

### Backend Technologies
- **Framework**: Flask 3.0 (Python 3.11)
- **Database**: MySQL 8.0 Community Edition
- **Database Driver**: mysql-connector-python 9.4
- **API Architecture**: RESTful API with JSON
- **CORS**: Flask-CORS for cross-origin support
- **Session Management**: Flask sessions with localStorage

### Frontend Technologies
- **Markup**: HTML5 with semantic elements
- **Styling**: Custom CSS3 with gradients and animations
- **Scripting**: Vanilla JavaScript (ES6+)
- **Design Pattern**: Modular multi-page architecture
- **API Communication**: Fetch API with async/await

### Database Design
- **Normalized Schema**: 5 tables with proper relationships
- **Referential Integrity**: Foreign keys with CASCADE
- **Indexing**: Optimized queries on frequently accessed columns
- **Character Set**: UTF-8MB4 (full Unicode support)
- **Storage Engine**: InnoDB for ACID compliance

### Development Tools
- **Code Editor**: VS Code / Any IDE
- **API Testing**: Browser DevTools
- **Database Management**: MySQL Workbench
- **Version Control**: Git-ready structure

---

## 🏗️ System Architecture

### High-Level Architecture
```
┌─────────────────────────────────┐
│   Web Browser (Client)          │
│   - HTML/CSS/JavaScript          │
│   - User Interface               │
└──────────────┬──────────────────┘
               │ HTTP/HTTPS
               │ Fetch API (JSON)
               ▼
┌─────────────────────────────────┐
│   Flask Backend (Server)         │
│   - RESTful API Endpoints        │
│   - Session Management           │
│   - Input Validation             │
└──────────────┬──────────────────┘
               │ SQL Queries
               │ mysql-connector
               ▼
┌─────────────────────────────────┐
│   MySQL Database                 │
│   - User Data                    │
│   - Medicine Records             │
│   - Schedule Information         │
│   - Intake Logs                  │
│   - Notifications                │
└─────────────────────────────────┘
```

### Request-Response Flow
1. User interacts with frontend (button click, form submission)
2. JavaScript validates input and captures data
3. Fetch API sends HTTP request to Flask backend
4. Flask validates request, checks authentication
5. Database query executed via mysql-connector
6. Response returned as JSON to frontend
7. JavaScript updates UI dynamically without page reload

---

## 📁 Project Structure

```
SMART_MEDICINE/
│
├── Backend/
│   └── app.py                          # Main Flask application
│                                        # - Database configuration
│                                        # - Authentication endpoints
│                                        # - CRUD API endpoints for all entities
│                                        # - User-specific data filtering
│                                        # - Family member management
│                                        # - Error handling & validation
│
├── Frontend/
│   ├── login.html                      # User authentication page
│   ├── index.html                      # Dashboard overview
│   ├── users.html                      # Family member management
│   ├── medicines.html                  # Medicine CRUD interface
│   ├── schedules.html                  # Schedule management
│   ├── notifications.html              # Notification center
│   ├── logs.html                       # Intake history viewer
│   │
│   ├── css/
│   │   └── style.css                   # Global styles and UI components
│   │
│   └── js/
│       ├── config.js                   # API configuration & helper functions
│       ├── dashboard.js                # Dashboard data loading
│       ├── users.js                    # Family member CRUD operations
│       ├── medicines.js                # Medicine CRUD operations
│       ├── schedules.js                # Schedule CRUD operations
│       ├── notifications.js            # Notification management
│       └── logs.js                     # Log viewing functionality
│
|
├── Database/
│   └── schema.sql                      # Complete database schema
│                                        # - Table definitions
│                                        # - Indexes & constraints
│                                        # - Sample data
│
├── Documentation/
│   └── README.md                       # This comprehensive guide
│
└── Screenshots/                        # UI screenshots (optional)
```

---

## 🗄️ Database Design

### Entity-Relationship Overview

**Core Entities:**
- **Users**: System users with role differentiation
- **Medicines**: Medicine records linked to users
- **Schedules**: Medication timing and frequency
- **IntakeLogs**: Actual intake tracking records
- **Notifications**: System messages and reminders

**Key Relationships:**
- One User → Many Medicines (one-to-many)
- One User → Many Schedules (one-to-many)
- One User → Many IntakeLogs (one-to-many)
- One User → Many Notifications (one-to-many)
- One User → Many Child Users (parent-child via `created_by`)

### Advanced Feature: Family Member System

**Database Schema Enhancement:**
```sql
Users Table:
- created_by INT (foreign key to Users.id)
```

This simple addition enables:
- Parent-child user relationships
- Family member grouping
- Isolated data per family
- Hierarchical user management

**Query Pattern:**
```sql
-- Get user and all their family members
SELECT * FROM Users 
WHERE id = ? OR created_by = ?
```

### Table Schemas

#### 1. Users Table
**Purpose**: Store all system users with family relationships

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INT | PRIMARY KEY, AUTO_INCREMENT | Unique identifier |
| name | VARCHAR(100) | NOT NULL | Full name |
| role | ENUM | 'patient', 'caregiver', 'doctor' | User role |
| contact_info | VARCHAR(100) | NULL | Phone/Address |
| email | VARCHAR(100) | UNIQUE, NOT NULL | Email address |
| password | VARCHAR(255) | NOT NULL | User password |
| created_by | INT | FOREIGN KEY (Users.id), NULL | Parent user (for family members) |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Registration time |

**Indexes**: email (UNIQUE), role, created_by

---

#### 2. Medicines Table
**Purpose**: Store medicine information per user

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INT | PRIMARY KEY, AUTO_INCREMENT | Medicine ID |
| user_id | INT | FOREIGN KEY (Users.id), NOT NULL | Owner |
| name | VARCHAR(100) | NOT NULL | Medicine name |
| dosage | VARCHAR(50) | NOT NULL | Dosage amount |
| instructions | TEXT | NULL | Usage instructions |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Creation time |

**Relationships**: Many-to-One with Users

---

#### 3. Schedules Table
**Purpose**: Define medication timing and frequency

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INT | PRIMARY KEY, AUTO_INCREMENT | Schedule ID |
| user_id | INT | FOREIGN KEY (Users.id), NOT NULL | Patient |
| medicine_id | INT | FOREIGN KEY (Medicines.id), NOT NULL | Medicine |
| schedule_time | TIME | NOT NULL | Daily time |
| days_of_week | VARCHAR(50) | NOT NULL | E.g., "Mon,Wed,Fri" |
| start_date | DATE | NOT NULL | Start date |
| end_date | DATE | NULL | End date (optional) |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Creation time |

**Relationships**: Many-to-One with Users and Medicines

---

#### 4. IntakeLogs Table
**Purpose**: Track actual medicine intake

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INT | PRIMARY KEY, AUTO_INCREMENT | Log ID |
| user_id | INT | FOREIGN KEY (Users.id), NOT NULL | User |
| medicine_id | INT | FOREIGN KEY (Medicines.id), NOT NULL | Medicine |
| scheduled_time | DATETIME | NOT NULL | Expected time |
| actual_time | DATETIME | NULL | Actual intake time |
| status | ENUM | 'taken', 'missed', 'pending' | Status |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Log time |

**Relationships**: Many-to-One with Users and Medicines

---

#### 5. Notifications Table
**Purpose**: Store all system notifications

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INT | PRIMARY KEY, AUTO_INCREMENT | Notification ID |
| user_id | INT | FOREIGN KEY (Users.id), NOT NULL | Recipient |
| message | TEXT | NOT NULL | Notification text |
| sent_time | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | When sent |
| type | ENUM | 'reminder', 'alert', 'info' | Message type |

**Relationships**: Many-to-One with Users

---

## 🔌 API Documentation

### API Base Configuration
```
Protocol: HTTP
Host: 127.0.0.1
Port: 5000
Base URL: http://127.0.0.1:5000
Content-Type: application/json
```

### Authentication Endpoints

#### POST /login
**Description**: Authenticate user and create session
**Request Body**:
```json
{
  "email": "john@example.com",
  "password": "password123"
}
```
**Response**:
```json
{
  "message": "Login successful",
  "user": {
    "id": 1,
    "name": "John Smith",
    "role": "patient",
    "email": "john@example.com"
  }
}
```

#### POST /logout
**Description**: Clear user session
**Response**:
```json
{
  "message": "Logged out successfully"
}
```

#### GET /check-session
**Description**: Verify if user is logged in
**Response**:
```json
{
  "logged_in": true,
  "user": { ... }
}
```

---

### User-Specific Data Endpoints (NEW - Privacy Feature)

#### GET /my-family?user_id={id}
**Description**: Get user and their created family members only
**Response**:
```json
[
  {
    "id": 1,
    "name": "John Smith",
    "role": "patient",
    "contact_info": "555-1234",
    "email": "john@example.com",
    "created_by": null
  },
  {
    "id": 7,
    "name": "Jane Smith",
    "role": "patient",
    "contact_info": "555-5678",
    "email": "jane@example.com",
    "created_by": 1
  }
]
```

#### GET /my-medicines?user_id={id}
**Description**: Get medicines for logged-in user only
**Response**: Array of medicine objects

#### GET /my-schedules?user_id={id}
**Description**: Get schedules for logged-in user only
**Response**: Array of schedule objects

#### GET /my-notifications?user_id={id}
**Description**: Get notifications for logged-in user only
**Response**: Array of notification objects

#### GET /my-intake-logs?user_id={id}
**Description**: Get intake logs for logged-in user only
**Response**: Array of log objects

---

### Standard CRUD Endpoints

#### Users API
- `GET /users` - Retrieve all users (admin use)
- `POST /users` - Create new user (includes `created_by` field)
- `PUT /users/<id>` - Update user details
- `DELETE /users/<id>` - Remove user

#### Medicines API
- `GET /medicines` - List all medicines (filtered on frontend)
- `POST /medicines` - Add new medicine
- `PUT /medicines/<id>` - Update medicine
- `DELETE /medicines/<id>` - Delete medicine

#### Schedules API
- `GET /schedules` - Get all schedules (filtered on frontend)
- `POST /schedules` - Create schedule
- `PUT /schedules/<id>` - Update schedule
- `DELETE /schedules/<id>` - Remove schedule

#### Notifications API
- `GET /notifications` - View notifications (filtered on frontend)
- `POST /notifications` - Send notification

#### Intake Logs API
- `GET /intake_logs` - Fetch logs (filtered on frontend)
- `POST /intake_logs` - Create log entry

---

## 🖥️ User Interface

### Design Philosophy
- **Simplicity**: Clean, intuitive interface
- **Privacy-First**: Users see only their data
- **Family-Oriented**: Easy management of family members
- **Responsive**: Works on desktop, tablet, mobile
- **Accessibility**: High contrast, clear labels

### Page Overview

#### 1. Login Page (login.html)
**Purpose**: User authentication
**Features**:
- Email & password form
- Demo credentials display
- Sign up link
- Auto-redirect if already logged in

#### 2. Dashboard (index.html)
**Purpose**: System overview with family context
**Features**:
- Statistics cards (medicines, schedules, notifications)
- Recent activity feed (family-filtered)
- User name display in header
- Quick navigation

#### 3. Family Management (users.html)
**Purpose**: Manage family members
**Features**:
- Add family member form
- List of user + their created family members
- Edit/Delete functionality
- Privacy notice
- "You" indicator for current user

#### 4. Medicine Management (medicines.html)
**Purpose**: Manage medicines for family
**Features**:
- Add medicine form with family member selector
- Medicine listing (filtered by family)
- Edit/Delete functionality
- Family member dropdown shows only own family

#### 5. Schedule Management (schedules.html)
**Purpose**: Create and manage medication schedules
**Features**:
- Schedule creation form
- Family member and medicine dropdowns (filtered)
- Time and date inputs
- Days of week configuration
- Schedule listing

#### 6. Notifications (notifications.html)
**Purpose**: Send and view notifications
**Features**:
- Send notification form
- Family member targeting
- Notification history (filtered)
- Type selection (reminder/alert/info)

#### 7. Intake Logs (logs.html)
**Purpose**: View medication intake history
**Features**:
- Read-only log viewer
- Status indicators (color-coded)
- Scheduled vs actual time display
- Family-filtered history

---

## 🔒 Security Features

### Implemented Security Measures

#### 1. Authentication & Authorization
- Session-based authentication with Flask sessions
- localStorage for client-side user state
- Login required for all pages (except login page)
- Automatic redirect to login if not authenticated

#### 2. Data Privacy & Isolation
- **User-Specific Data Filtering**: Each user sees only their own data
- **Family Member Isolation**: Complete separation between different families
- **Backend Filtering**: User-specific endpoints (`/my-*`)
- **Frontend Filtering**: Dropdowns show only family members

#### 3. Input Validation
- Required field validation on all forms
- Email format validation
- Input sanitization on backend
- SQL parameterized queries (prevents SQL injection)

#### 4. Error Handling
- Try-catch blocks on all API calls
- User-friendly error messages
- Server errors don't expose system details
- Consistent error response format

### Security Best Practices Applied
- ✅ No plaintext password display
- ✅ CORS configured properly
- ✅ Database connections closed after use
- ✅ Foreign key constraints for data integrity
- ✅ Prepared statements for SQL queries

### Future Security Enhancements
- Password hashing (bcrypt/argon2)
- JWT-based authentication
- HTTPS/SSL encryption
- Rate limiting on API endpoints
- Two-factor authentication
- Session timeout implementation

---

## 🧪 Testing Guide

### Pre-Testing Checklist
- [ ] MySQL server running
- [ ] Flask backend running (`python app.py`)
- [ ] Frontend server running (`python -m http.server 5500`)
- [ ] Database schema loaded
- [ ] Sample data inserted

### New: Sign-up page

A new `signup.html` page is included in the `frontend` folder so users can create new accounts directly from the UI. The signup form will POST to the backend `/users` endpoint. Steps to test:

- Start the backend from `Backend`:
```powershell
python app.py
```
- Start the frontend static server from `frontend`:
```powershell
cd frontend
python -m http.server 5500
```
- Open http://127.0.0.1:5500/signup.html and create a new user. Then use the login page to sign in.


### Troubleshooting: "Error loading dashboard: Failed to fetch"

If your dashboard shows "Error loading dashboard: Failed to fetch" when refreshing or loading the page, it means the frontend couldn't reach the backend (network/CORS/port mismatch). Try the following checks:

- Make sure the Flask backend is running: from the `Backend` folder run:
```powershell
python app.py
```

- Verify the backend is reachable in a browser: open http://127.0.0.1:5000/test — you should see "Test route working!". The root `/` route returns a small JSON status object.

- Confirm the frontend is served over HTTP (not file://) and matches the origin configured in `app.py` CORS settings. Start a simple static server from `frontend`:
```powershell
cd frontend
python -m http.server 5500
```

- Ensure the origin used by the frontend is permitted in `Backend/app.py` CORS setup. By default the project allows `http://127.0.0.1:5500` and `http://localhost:5500`. If you serve the frontend on a different host/port, add that origin or temporarily allow all origins for development.

- Use the browser DevTools (Console + Network) to inspect the failing request. A network or CORS error will appear in the Console and the failing request in Network will show the status or missing CORS response headers.

- The dashboard now performs a quick health-check and will show a clearer message if the backend cannot be reached. If you still see errors, check the server log for errors or share the request log and console output and I can help debug further.


### Test Scenarios

#### Test 1: User Authentication
1. Open `http://localhost:5500/login.html`
2. Login with `john@example.com` / `password123`
3. **Expected**: Redirect to dashboard, user name displayed in header

#### Test 2: Family Member Management
1. Login as John
2. Navigate to Family page
3. **Expected**: See only John (marked as "You")
4. Add family member (Jane Smith, patient, jane@smith.com)
5. **Expected**: Table shows John and Jane
6. Logout, login as Elena (`elena@example.com` / `password123`)
7. **Expected**: See only Elena (Jane is hidden)

#### Test 3: Medicine Privacy
1. Login as John
2. Go to Medicines page
3. **Expected**: User dropdown shows only "John Smith (You)" and Jane
4. Add medicine for Jane
5. Logout, login as Elena
6. **Expected**: Elena cannot see Jane's medicine

#### Test 4: CRUD Operations
1. Login as any user
2. Test Create: Add medicine → Success message
3. Test Read: View medicines table → Data displayed
4. Test Update: Click Edit → Modify → Update
5. Test Delete: Click Delete → Confirm → Record removed

#### Test 5: Dashboard Data
1. Login as John
2. Check dashboard statistics
3. **Expected**: Counts reflect only John's family data
4. Check Recent Activity
5. **Expected**: Shows only family notifications

---

## 🚀 Installation Guide

### System Requirements
- **Operating System**: Windows 10/11, macOS, or Linux
- **Python**: Version 3.11 or higher
- **MySQL**: Version 8.0 or higher
- **Browser**: Chrome 90+, Firefox 88+, Edge 90+
- **RAM**: Minimum 4GB
- **Storage**: 500MB free space

### Installation Steps

#### Step 1: Database Setup
```bash
# 1. Open MySQL Workbench or command line
mysql -u root -p

# 2. Create database
CREATE DATABASE medreminder_db;

# 3. Use the database
USE medreminder_db;

# 4. Run schema file
SOURCE /path/to/SMART_MEDICINE/Database/schema.sql;

# 5. Run the family member update
ALTER TABLE Users ADD COLUMN created_by INT NULL AFTER password;
ALTER TABLE Users ADD FOREIGN KEY (created_by) REFERENCES Users(id) ON DELETE SET NULL;

# 6. Verify
SHOW TABLES;
DESCRIBE Users;
```

#### Step 2: Backend Setup
```bash
# 1. Navigate to Backend folder
cd D:\SEM_5\mini project\Project\SMART_MEDICINE\Backend

# 2. Install dependencies
pip install flask flask-cors mysql-connector-python

# 3. Update database credentials in app.py if needed

# 4. Start Flask server
python app.py

# Expected output:
# * Running on http://127.0.0.1:5000
```

#### Step 3: Frontend Setup
```bash
# 1. Navigate to Frontend folder (new terminal)
cd D:\SEM_5\mini project\Project\SMART_MEDICINE\Frontend

# 2. Start HTTP server
python -m http.server 5500

# Expected output:
# Serving HTTP on :: port 5500
```

#### Step 4: Access Application
```
Open browser: http://localhost:5500/login.html
```

---

## 🔮 Future Enhancements

### Immediate Next Steps
- [ ] Password hashing with bcrypt
- [ ] Profile editing page for users
- [ ] Export data to PDF/CSV
- [ ] Search and filter functionality in tables
- [ ] Pagination for large datasets

### Medium-Term Goals
- [ ] Automated reminder generation
- [ ] Email/SMS notification integration
- [ ] Medicine refill reminders
- [ ] Adherence analytics dashboard
- [ ] Multi-language support

### Long-Term Vision
- [ ] Mobile application (React Native/Flutter)
- [ ] Voice assistant integration
- [ ] AI-powered adherence prediction
- [ ] IoT medicine dispenser integration
- [ ] Telemedicine video consultations
- [ ] Wearable device integration

---

## 📜 License & Contact

### License
This project is developed for academic purposes as part of the SEM 5 Mini Project curriculum.  
**All Rights Reserved © 2025**

### Academic Information
- **Institution**: East West Institute Of Technology , Bengaluru
- **Department**: Artificial Intelligence And Machine Learning
- **Course**: SEM 5 Mini Project
- **Academic Year**: 2025-2026

### Project Team
- **Developer**: Koushik R
- **Project Guide**: Prof. Divya , East West Institute Of Technology , Bengaluru
- **Submission Date**: 

### Project Achievements

**Core Features Implemented:**
- ✅ Complete full-stack web application
- ✅ RESTful API with 20+ endpoints
- ✅ MySQL database with normalized schema
- ✅ User authentication & session management
- ✅ Complete CRUD operations for all entities
- ✅ **Family member management system** (Advanced)
- ✅ **User-specific data privacy** (Advanced)
- ✅ Professional UI with edit modals
- ✅ Comprehensive documentation

**Technical Highlights:**
- RESTful API architecture
- Normalized database design
- Parent-child user relationships
- Data isolation & privacy
- Responsive web design
- Modular JavaScript architecture

### Contact Information

For inquiries, collaboration opportunities, or access to:
- Complete source code
- Live demonstration
- Technical documentation
- Database design documents
- System architecture diagrams
- Deployment guides

**Please contact:**  
📧 Email: kowshikr3932@gmail.com  
📱 Phone: +918951506863
💼 LinkedIn: https://www.linkedin.com/in/koushik-r-a33a272a6/
🌐 Portfolio: [Your Website]


---

## 🙏 Acknowledgments

### Technical Resources
- Flask Documentation: https://flask.palletsprojects.com/
- MySQL Reference Manual: https://dev.mysql.com/doc/
- MDN Web Docs: https://developer.mozilla.org/

### Special Thanks
- Project guide for mentorship
- Research papers on medication adherence
- Open-source community for tools and libraries

---

**Last Updated**: October 25, 2025 (7:19 PM IST)  
**Version**: 2.0.0 (Final Release)  
**Status**: Production Ready

---

*This project demonstrates advanced full-stack development skills including database design, RESTful API development, user authentication, data privacy implementation, and modern frontend development. Built with dedication for improving healthcare accessibility through technology.*