*# Gym Management System*



*A web-based Gym Management System designed to help gym owners manage members and track monthly payments efficiently.*



*## Features*



*\* Add new gym members*

*\* Validate mobile numbers with exactly 10 digits*

*\* View all registered members*

*\* Edit member details*

*\* Record member payments*

*\* View payment history*

*\* Track pending payments*

*\* Support partial payments*

*\* Automatically calculate total due amount*

*\* Automatically calculate total paid and pending balance*

*\* Dashboard showing total members, collections, and pending payments*



*## Partial Payment Example*



*Suppose a member has:*



*\* Monthly Fee: ₹1500*

*\* Total Amount Due: ₹3000*

*\* Amount Paid: ₹1500*



*The system correctly shows:*



*\* Total Paid: ₹1500*

*\* Pending Amount: ₹1500*

*\* Status: Partially Paid*



*This helps prevent a member from being incorrectly marked as fully paid when they have an outstanding balance.*



*## Technologies Used*



*### Frontend*



*\* HTML*

*\* CSS*

*\* JavaScript*



*### Backend*



*\* Python*

*\* FastAPI*



*### Database*



*\* SQLite*



*## Project Structure*



*```text*

*GymManagementWeb/*

*│*

*├── backend/*

*│   ├── app.py*

*│   ├── requirements.txt*

*│*

*├── frontend/*

*│   └── index.html*

*│*

*├── .gitignore*

*└── README.md*

*```*



*## How to Run the Project*



*### 1. Start the Backend*



*Open PowerShell and go to the backend folder:*



*```powershell*

*cd backend*

*```*



*Activate the virtual environment:*



*```powershell*

*.\\venv\\Scripts\\Activate.ps1*

*```*



*Install the required packages:*



*```powershell*

*pip install -r requirements.txt*

*```*



*Start the FastAPI server:*



*```powershell*

*uvicorn app:app --reload*

*```*



*The backend will run on:*



*`http://127.0.0.1:8000`*



*### 2. Start the Frontend*



*Open another PowerShell window and go to the frontend folder:*



*```powershell*

*cd frontend*

*```*



*Start a local server:*



*```powershell*

*python -m http.server 5500*

*```*



*Open the website in your browser:*



*`http://127.0.0.1:5500`*



*## Future Improvements*



*\* User login for gym owners*

*\* Automatic payment reminders*

*\* Cloud database deployment*

*\* Mobile-friendly version*

*\* Online payment integration*



*## Author*



*\*\*Rupesh\*\**



*---*



*This project was developed as a practical web application to solve real-world gym member and payment management problems.*



