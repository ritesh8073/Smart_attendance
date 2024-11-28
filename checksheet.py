from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials

SCOPES = ['https://www.googleapis.com/auth/drive']
SERVICE_ACCOUNT_FILE = 'credentials.json'  # Replace with your credentials file path

creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
drive_service = build('drive', 'v3', credentials=creds)

# List file IDs you want to check
file_ids = [
    "10C1xyVdydJcBt8HnO893wyXq4AUcc215LIG8Q7naMdY",  # Example file ID
    "15yAsh3XY3zP9khY2PdBOoK0k0twWQBzVZF8uAQCa-P4",  # Example file ID
    # Add more file IDs here to check
]

for file_id in file_ids:
    try:
        file = drive_service.files().get(fileId=file_id).execute()
        print(f"File {file_id} exists: {file['name']}")
    except Exception as e:
        print(f"File {file_id} does not exist or has been deleted.")
