import argparse
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials
from googleapiclient.errors import HttpError

# Set up Google Sheets API credentials and the Spreadsheet ID
SERVICE_ACCOUNT_FILE = 'credentials.json'  # Path to your service account credentials file
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

# Authenticate with Google Sheets API
def authenticate_google_sheets():
    creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    return build('sheets', 'v4', credentials=creds)

# Function to clear data from all sheets in the spreadsheet
def clear_all_data(spreadsheet_id):
    try:
        # Authenticate with the API
        service = authenticate_google_sheets()

        # Get spreadsheet metadata to get all the sheet names
        spreadsheet_metadata = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()

        # Extract sheet names (or sheetId) for each sheet in the spreadsheet
        sheet_names = [sheet['properties']['title'] for sheet in spreadsheet_metadata['sheets']]

        # Clear data from all sheets
        for sheet in sheet_names:
            range_to_clear = f'{sheet}!A:Z'  # Clears columns A to Z (you can adjust the range if needed)
            request = service.spreadsheets().values().clear(
                spreadsheetId=spreadsheet_id,
                range=range_to_clear
            )
            request.execute()

        print(f"All data cleared successfully from the spreadsheet: {spreadsheet_id}")

    except HttpError as err:
        print(f"Error clearing data: {err}")

def main():
    # Set up the command-line argument parser
    parser = argparse.ArgumentParser(description='Clear all data in all sheets of a Google Spreadsheet.')
    parser.add_argument('spreadsheet_id', help='The ID of the Google Spreadsheet you want to clear data from.')

    # Parse the arguments
    args = parser.parse_args()

    # Call the function to clear data from the provided spreadsheet_id
    clear_all_data(args.spreadsheet_id)

if __name__ == '__main__':
    main()
