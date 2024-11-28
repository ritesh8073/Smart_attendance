import os
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2.service_account import Credentials

# Define your service account file path and scopes
SERVICE_ACCOUNT_FILE = 'credentials.json'  # Path to your service account credentials
SCOPES = ['https://www.googleapis.com/auth/drive']

# Initialize the Google Drive API client
def initialize_drive_service():
    creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    return build('drive', 'v3', credentials=creds)

# Function to list and delete all Google Sheets
def delete_all_google_sheets():
    try:
        # Initialize the Google Drive API
        service = initialize_drive_service()

        # Query to list all Google Sheets files
        results = service.files().list(
            q="mimeType='application/vnd.google-apps.spreadsheet'",  # Query to get only Google Sheets
            fields="files(id, name)"
        ).execute()

        # Get the list of Google Sheets files
        sheets = results.get('files', [])

        if not sheets:
            print('No Google Sheets found.')
        else:
            print(f"Found {len(sheets)} Google Sheets. Deleting...")

            # Iterate through each sheet and delete it
            for sheet in sheets:
                sheet_id = sheet['id']
                sheet_name = sheet['name']

                # Delete the Google Sheet file
                service.files().delete(fileId=sheet_id).execute()
                print(f"Deleted: {sheet_name} (ID: {sheet_id})")

            print("All Google Sheets have been deleted.")
    
    except HttpError as error:
        print(f"An error occurred: {error}")

# Run the function to delete all Google Sheets
if __name__ == '__main__':
    delete_all_google_sheets()
