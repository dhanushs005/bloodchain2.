import random
import string
from django.shortcuts import redirect
from django.http import HttpResponse
from django.shortcuts import render
from django.http import JsonResponse
from .forms import UserForm, EmergencyForm, ReportForm, LoginForm, SignupForm
from pymongo import MongoClient

# MongoDB connection setup
MONGO_URI = "mongodb+srv://Dhanush:2k22ca005@userdetails.mavp0oq.mongodb.net/?retryWrites=true&w=majority&appName=userdetails" # Update with your MongoDB URI
DB_NAME = "Users"  # Replace with your database name
USER_COLLECTION = "User"  # Replace with your user collection name
EMERGENCY_COLLECTION = "emergency"  # Replace with your emergency collection name
REPORTS_COLLECTION = "reports"  # The reports collection
LOGS_COLLECTION = "logs" #Login details collection
# Initialize MongoDB client
client = MongoClient(MONGO_URI)
db = client[DB_NAME]

# Home view
def home(request):
    return render(request, 'Main/home.html',)

def donate(request):
    user_id = request.COOKIES.get("user_id")
    if user_id == None:
        lform = LoginForm()
        return render(request, 'Main/profile-login.html', {'form': lform})
    else:
        form = UserForm()
        return render(request, 'Main/donate.html', {'UserForm': form})
def report(request):
    user_id = request.COOKIES.get("user_id")
    if user_id == None:
        lform = LoginForm()
        return render(request, 'Main/profile-login.html', {'form': lform})
    else:
        form3 = ReportForm()
        return render(request, 'Main/report.html',{'ReportForm':form3})
# Emergency view
def emerg(request):
    user_id = request.COOKIES.get("user_id")
    if user_id == None:
        lform = LoginForm()
        return render(request, 'Main/profile-login.html', {'form': lform})
    else:
        form2 = EmergencyForm()
        return render(request, 'Main/emergency.html', {'EmergencyForm': form2})

def login(request):
    lform = LoginForm()  # Instantiate the form
    return render(request, 'Main/profile-login.html', {'form': lform})

def signup(request):
    sform = SignupForm()  # Instantiate the form
    return render(request, 'Main/profile-signup.html', {'form': sform})

def profile(request):
    user_id = request.COOKIES.get("user_id")

    if user_id is None:
        # If no user_id is found in cookies, handle appropriately (e.g., redirect to login)
        return redirect('login')  # Or render a login page if necessary

    # Query the database to fetch user details using the user_id from the LOGS_COLLECTION (for username, etc.)
    user = db[LOGS_COLLECTION].find_one({"user_id": user_id}, {"_id": 0, "username": 1, "password": 1})

    if user:
        username = user.get("username")
        # Avoid passing password to the template for security reasons
        password = "Password is secured"  # Placeholder text or you could hide it

        # Query the blood details from USER_BLOOD_COLLECTION based on the user_id
        blood_details = list(db[USER_COLLECTION].find({"user_id": user_id}, {"_id": 0,"name":1, "mobile":1, "blood_group": 1, "last_donated_date": 1, "district": 1}))

        if not blood_details:
            blood_details_message = "No blood donation details available."
        else:
            blood_details_message = None

        # Pass all user details and blood details to the template
        return render(request, 'Main/profile.html', {
            'username': username,
            'password': password,
            'blood_details': blood_details,
            'blood_details_message': blood_details_message
        })
    else:
        # Handle case where user does not exist (perhaps user_id is invalid)
        return redirect('login')  # Or render a "user not found" page

    # If there's no user_id cookie, render signup page with the SignupForm
    sform = SignupForm()  # Instantiate the form
    return render(request, 'Main/profile-signup.html', {'form': sform})
# View donors and emergency data
def view_donors(request):
    user_id = request.COOKIES.get("user_id")
    if user_id == None:
        lform = LoginForm()
        return render(request, 'Main/profile-login.html', {'form': lform})
    else:
        blood_group = request.GET.get('blood_group', '').strip()
        district = request.GET.get('district', '').strip()

            # Build MongoDB query based on search parameters
        query = {}
        if blood_group:
            query['blood_group'] = blood_group
        if district:
            query['district'] = district

            # Fetch matching donors and emergency cases
        donors = list(db[USER_COLLECTION].find(query, {"_id": 0}))
        emergency = list(db[EMERGENCY_COLLECTION].find({}, {"_id": 0}))  # Fetch all emergency cases

        context = {
            'donors': donors,
            'emergency': emergency,
        }
        return render(request, 'Main/donors.html', context)

# Save user details
def save_user_details(request):
    if request.method == 'POST':
        form = UserForm(request.POST)
        if form.is_valid():
            cleaned_data = form.cleaned_data
            mobile = cleaned_data['mobile']  # Mobile number field from the form
            user_id = request.COOKIES.get("user_id")
            # Check if the mobile number already exists in the database
            existing_user = db[USER_COLLECTION].find_one({"mobile": mobile})

            if existing_user:
                # If the mobile number exists, return an error
                return JsonResponse({"status": "error", "message": "Mobile number already exists!"})
            else:
                # If the mobile number is unique, save the data
                new_entry = {
                    "user_id": user_id,
                    "name": cleaned_data['name'],
                    "mobile": mobile,
                    "blood_group": cleaned_data['bg'],
                    "gender": cleaned_data['gender'],
                    "district": cleaned_data['dists'],
                    "last_donated_date": str(cleaned_data['last_date'])
                }
                try:
                    # Insert into MongoDB
                    db[USER_COLLECTION].insert_one(new_entry)
                    return JsonResponse({"status": "success", "message": "User details saved successfully!"})
                except Exception as e:
                    return JsonResponse({"status": "error", "message": f"Error saving data: {str(e)}"})
        else:
            return JsonResponse({"status": "error", "message": "Invalid form data!", "errors": form.errors})

    return render(request, 'form.html', {'form': UserForm()})
# Save emergency details
def emergency_details(request):
    if request.method == 'POST':
        form = EmergencyForm(request.POST)
        if form.is_valid():
            cleaned_data = form.cleaned_data
            new_entry = {
                "pname": cleaned_data['pname'],
                "pmobile": cleaned_data['pmobile'],
                "bg_needed": cleaned_data['bg_needed'],
                "pgender": cleaned_data['pgender'],
                "units_needed": cleaned_data['units_needed'],
                "hospital_name": cleaned_data['hospital_name'],
                "pdists": cleaned_data['pdists'],
                "urgency_level": cleaned_data['urgency_level']
            }
            try:
                # Insert into MongoDB
                db[EMERGENCY_COLLECTION].insert_one(new_entry)
                return JsonResponse({"status": "success", "message": "Emergency details saved successfully!"})
            except Exception as e:
                return JsonResponse({"status": "error", "message": f"Error saving data: {str(e)}"})
        else:
            return JsonResponse({"status": "error", "message": "Invalid form data!", "errors": form.errors})
    return render(request, 'form.html', {'form': EmergencyForm()})

def updateReport(request):
    if request.method == 'POST':
        form = ReportForm(request.POST)
        if form.is_valid():
            # Extract cleaned data from the form
            cleaned_data = form.cleaned_data
            mobile = cleaned_data['rmobile']  # Mobile field
            report_type = cleaned_data['report_type']  # Report type field
            description = cleaned_data['description']  # Description field

            new_entry = {
                "mobile": mobile,
                "report_type": report_type,
                "description": description,
            }

            try:
                # Insert into MongoDB
                db[REPORTS_COLLECTION].insert_one(new_entry)
                return JsonResponse({"status": "success", "message": "Report saved successfully!"})
            except Exception as e:
                return JsonResponse({"status": "error", "message": f"Error saving data: {str(e)}"})
        else:
            return JsonResponse({"status": "error", "message": "Invalid form data!", "errors": form.errors})

    # For GET requests, render the ReportForm
    form = ReportForm()
    return render(request, 'form.html', {'form': form})


def save_logs(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            cleaned_data = form.cleaned_data
            username = cleaned_data['username']

            # Check if the username already exists in the database
            existing_user = db[LOGS_COLLECTION].find_one({"username": username})

            if existing_user:
                # If the username exists, return an error
                return JsonResponse({"status": "error", "message": "Username already exists!"})
            else:
                # If the username is unique, save the data
                user_id = request.COOKIES.get("user_id")
                new_entry = {
                    "user_id": user_id,
                    "username": cleaned_data['username'],
                    "password": cleaned_data['password']
                }
                try:
                    # Insert into MongoDB
                    db[LOGS_COLLECTION].insert_one(new_entry)
                    return JsonResponse({"status": "success", "message": "User details saved successfully!"})
                except Exception as e:
                    return JsonResponse({"status": "error", "message": f"Error saving data: {str(e)}"})
        else:
            return JsonResponse({"status": "error", "message": "Invalid form data!", "errors": form.errors})

    return render(request, 'form.html', {'form': LoginForm()})


def generate_session_token(length=16):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choices(characters, k=length))

def login_user(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            cleaned_data = form.cleaned_data
            username = cleaned_data['username']
            password = cleaned_data['password']

            # Check if the user exists in the database
            user = db[LOGS_COLLECTION].find_one({"username": username, "password": password})

            if user:
                # Generate a random session token
                session_token = generate_session_token()

                # Set the token as a cookie
                response = JsonResponse({"status": "success", "message": "Login successful!"})
                response.set_cookie("user_id", session_token, httponly=True, max_age=2592000)  # Cookie valid for 30 days
                return response
            else:
                return JsonResponse({"status": "error", "message": "Invalid username or password!"})
        else:
            return JsonResponse({"status": "error", "message": "Invalid form data!", "errors": form.errors})

    return render(request, 'login.html', {'form': LoginForm()})

def disp_user(request):
    user_id = request.COOKIES.get("user_id")

    if user_id is None:
        # If no user_id is found in cookies, handle appropriately (e.g., redirect to login)
        return redirect('login')  # Or render a login page if necessary

    # Query the database to fetch user details using the user_id from the LOGS_COLLECTION (for username, etc.)
    user = db[LOGS_COLLECTION].find_one({"user_id": user_id}, {"_id": 0, "username": 1, "password": 1})

    if user:
        username = user.get("username")
        # Avoid passing password to the template for security reasons
        password = "Password is secured"  # Placeholder text or you could hide it

        # Query the blood details from USER_BLOOD_COLLECTION based on the user_id
        blood_details = list(db[USER_COLLECTION].find({"user_id": user_id}, {"_id": 0, "blood_group": 1, "donation_date": 1, "district": 1}))

        if not blood_details:
            blood_details_message = "No blood donation details available."
        else:
            blood_details_message = None

    else:
        # Handle case where user does not exist (perhaps user_id is invalid)
        return redirect('login')  # Or render a "user not found" page

    # Pass all user details and blood details to the template
    return render(request, 'Main/profile.html', {
        'username': username,
        'password': password,
        'blood_details': blood_details,
        'blood_details_message': blood_details_message
    })

def logout(request):
    # Create an HttpResponse object to indicate the logout action
    response = HttpResponse("Logged out successfully.")

    # Delete cookies from the response
    response.delete_cookie('user_id')  # Delete the 'user_id' cookie

    # Redirect the user to the login page after deleting cookies
    return redirect('login')  # Redirect to your login page or another page as needed# def view_reports(request):
#     blood_group = request.GET.get('blood_group', '').strip()
#     district = request.GET.get('district', '').strip()
#
#     # Build MongoDB query based on search parameters
#     query = {}
#     if blood_group:
#         query['blood_group'] = blood_group
#     if district:
#         query['district'] = district
#
#     # Fetch matching donors and emergency cases
#     donors = list(db[USER_COLLECTION].find(query, {"_id": 0}))
#     emergency = list(db[EMERGENCY_COLLECTION].find({}, {"_id": 0}))  # Fetch all emergency cases
#
#     context = {
#         'donors': donors,
#         'emergency': emergency,
#     }
#     return render(request, 'Main/donors.html', context)
