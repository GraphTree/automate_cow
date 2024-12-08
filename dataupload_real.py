import os.path
import pandas as pd
import numpy as np

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# This line defines what permissions our application needs to access Google Sheets
# If you change these permissions, you'll need to delete token.json and re-authenticate
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

# These are important identifiers for your Google Sheet
# SAMPLE_SPREADSHEET_ID is the unique ID of your Google Sheet - you can find this in the URL when you open your sheet
# SAMPLE_RANGE_NAME is which sheet/tab we want to work with (in this case, "Sheet1")
SAMPLE_SPREADSHEET_ID = "14jU4irgCvBFlKqP9_PceMIOlv5rEnokp3-5RXglcdgg"
SAMPLE_RANGE_NAME = "Sheet1"

def find_first_empty_row(sheet, spreadsheet_id):
    """This function looks through your Google Sheet to find the first empty row.
    It does this by checking column A from top to bottom.
    This is useful because we want to add new data without overwriting existing data."""
    try:
        # We ask Google Sheets API to give us all values in column A
        # The range "A:A" means "all of column A"
        result = sheet.values().get(
            spreadsheetId=spreadsheet_id,
            range=f"{SAMPLE_RANGE_NAME}!A:A"  # Check column A
        ).execute()
        values = result.get('values', [])
        
        # We go through each row in column A
        # Row numbers in Google Sheets start at 1
        row = 1
        for value in values:
            # If we find an empty row or row with just spaces, that's our first empty row
            if not value or not value[0].strip():
                return row
            row += 1
        # If all rows have data, we'll return the next row number after the last data
        return row
        
    except HttpError as err:
        # If something goes wrong (like internet connection issues), we print the error
        print(f"Error checking rows: {err}")
        return None


def readGmarket():
    # Read the Excel file
    df = pd.read_excel('./cow_file/gmarket.xlsx')
    
    # Convert timestamp columns to string format
    for col in df.select_dtypes(include=['datetime64[ns]']).columns:
        df[col] = df[col].astype(str)
    
    # Get column headers
    headers = df.columns.tolist()
    
    # Convert data to list of lists, including headers as first row
    valueData = [headers]  # Add headers as first row
    
    # Convert DataFrame to list of lists, replacing NaN with empty string
    data_rows = df.replace({np.nan: ''}).values.tolist()
    valueData.extend(data_rows)
    
    print("Data to be uploaded:")
    print(f"Headers: {headers}")
    print(f"Number of rows: {len(valueData)-1}")  # -1 to exclude header row
    print(valueData)
    return valueData


def main():
    """This is the main function that does all the work.
    It reads data from an Excel file and puts it into your Google Sheet."""
    
    # First, we need to handle authentication (proving you have permission to access the sheet)
    creds = None
    
    # We check if we already have a token.json file with valid credentials
    # token.json contains your access permissions - like a digital key
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    
    # If we don't have valid credentials, we need to get them
    if not creds or not creds.valid:
        # If credentials expired but we can refresh them, do that
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # If we need completely new credentials:
            # 1. Read the client secrets from credentials.json (your API key details)
            # 2. Open a web browser for you to log in to your Google account
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json", SCOPES
            )
            creds = flow.run_local_server(port=3000)
        
        # Save the new credentials to token.json for next time
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    try:
        # Create a connection to the Google Sheets API
        service = build("sheets", "v4", credentials=creds)
        sheet = service.spreadsheets()

        # Find where we should start adding new data
        first_empty_row = find_first_empty_row(sheet, SAMPLE_SPREADSHEET_ID)
        
        # If we couldn't find an empty row, stop the program
        if first_empty_row is None:
            print("Error finding empty row")
            return

        # Read your Excel file named 'gmarket.xlsx' into a pandas DataFrame
        # Then convert it to a list of lists that Google Sheets can understand
        valueData = readGmarket()

        # Create the range where we'll insert data
        # For example, if first_empty_row is 5, this will be "Sheet1!A5"
        update_range = f"{SAMPLE_RANGE_NAME}!A{first_empty_row}"

        print(f"Inserting data starting at row {first_empty_row}")
        
        # Finally, send the data to Google Sheets
        # - spreadsheetId: tells which spreadsheet to update
        # - range: tells where to put the data
        # - valueInputOption: "USER_ENTERED" means treat the data like a user typed it
        # - body: the actual data to insert
        result = (
            sheet.values()
            .update(
                spreadsheetId=SAMPLE_SPREADSHEET_ID,
                range=update_range,
                valueInputOption="USER_ENTERED",
                body={"values": valueData}
            )
            .execute()
        )
        # Print how many cells we updated
        print(f"Updated {result.get('updatedCells')} cells")

    except HttpError as err:
        # If anything goes wrong with the API calls, print the error
        print(err)


# This line checks if we're running this file directly (not importing it)
# If we are, run the main() function
if __name__ == "__main__":
    # main()
    readGmarket()
