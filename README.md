📦 Courier Service Management System

Overview
The Courier Service Management System is a Django-based web application designed to simplify courier operations. It enables parcel booking, tracking, and management through a clean, responsive interface built with HTML, CSS, JavaScript, and Bootstrap.

---

✨ Features
- Parcel Booking: Customers can book parcels with sender and receiver details.
- Parcel Tracking: Real-time status updates (Booked, In Transit, Delivered).
- User Roles:
  - Customer App: Interface for booking and tracking parcels.
  - Main App: This is the main app faced while you open the website.
- Responsive UI: Built with Bootstrap for mobile and desktop compatibility.
- Authentication: Secure login and registration system.

---

🛠️ Tech Stack
- Frontend: HTML, CSS, JavaScript, Bootstrap
- Backend: Python, Django
- Database: SQLite (default)
- Authentication: Django’s built-in auth system

---

📂 Project Structure
`
├──
│   ├── CourierServiceMgmt/         # app for settings and basic requirements 
│   ├── customer/     # Customer-facing app
│   ├── main/       # this is the main app faced while you open the website
│   ├── static/    # user images
│   ├── manage.py     # Django project manager
│   └── db.sqlite3   # default database
└──
`

---

🚀 Installation & Setup
1. Clone the repository:
   `bash
   git clone (https://github.com/yash-vtg/Courier_Service_Management_System.git)
   cd courier-service-management
   `
2. Create and activate a virtual environment:
   `bash
   python -m venv venv
   source venv/bin/activate   # Linux/Mac
   venv\Scripts\activate      # Windows
   `
3. Apply migrations:
   `   python manage.py migrate
   `
4. Create a superuser (for admin access):
   `   python manage.py createsuperuser
   `
5. Run the server:
   `   python manage.py runserver
   `
6. Access the app at http://127.0.0.1:8000/

---

📖 Usage
- Customers: Manage bookings, update parcel statuses, view reports, Book and track parcels via the customer app.
- Admins/Staff: use django administration portal.

---

✅ Future Enhancements
- Integration with SMS/email notifications
- Payment gateway support
- Route optimization for deliveries
- Multi-language support

---

🤝 Contributing
Contributions are welcome! Fork the repo, create a branch, and submit a pull request.
