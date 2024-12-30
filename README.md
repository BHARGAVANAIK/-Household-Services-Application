Problem Statement:
The Household Services Application is a multi-user platform designed to offer comprehensive
home services and solutions. This platform connects customers with service professionals,
allowing customers to request various services while professionals can accept or decline those
requests. The admin has full control of the platform, managing users, services, and requests.

Approach to the Problem Statement:
1. User Role Management:
Admin: Manages services, approves/rejects service professionals, and monitors all
activities.
Service Professional: Handles service requests by accepting or declining them and
delivering the requested services.
Customer: Creates, updates, and closes service requests and can leave reviews
post-service completion.
2. Service Request Flow:
Customers create a service request, which is assigned to service professionals. After the
service is completed, the customer closes the request and provides feedback.
3. Database Design:
A normalized database structure was implemented to maintain relationships between users,
services, and service requests. It ensures data integrity and operational efficiency.
4. Frontend and Backend Communication:
Flask serves as the backend framework for API development, and Bootstrap is used for
building a responsive, user-friendly interface.

Frameworks and Libraries Used:
The project utilized the following technologies:
Backend: Flask, Flask-SQLAlchemy, Flask-JWT-Extended, Celery, Redis
Frontend: Bootstrap and Axios for API interaction
Database: SQLite
