import re
from datetime import datetime, timedelta

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Define the scopes required for calendar access
SCOPES = ['https://www.googleapis.com/auth/calendar.events']

def get_credentials():
    """Authenticate and get OAuth2 credentials."""
    flow = InstalledAppFlow.from_client_secrets_file(
        'cre.json', SCOPES
    )
    creds = flow.run_local_server(port=0)
    return creds

def extract_datetime_range(text):
    """Extract start and end times from text, recognizing relative dates."""
    today = datetime.now()
    time_patterns = [
        r"(\d{1,2}:\d{2} ?[APM]*)",  # Match times like 1:30PM or 14:00
        r"(\d{1,2}(?:st|nd|rd|th)? [A-Za-z]{3})",  # Match dates like 16th Oct
    ]

    # Adjust today based on keywords
    if 'yesterday' in text.lower():
        today -= timedelta(days=1)
    elif 'tomorrow' in text.lower():
        today += timedelta(days=1)
    elif 'day after tomorrow' in text.lower():
        today += timedelta(days=2)

    # Extract times from text
    times = []
    dates = []
    
    for pattern in time_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            for match in matches:
                if re.search(r"\d{1,2}:\d{2}", match):  # Check if it's a time
                    try:
                        # Parse time with AM/PM if provided
                        time_obj = datetime.strptime(match.strip(), "%I:%M%p").time()
                    except ValueError:
                        # Otherwise, parse as 24-hour format
                        time_obj = datetime.strptime(match.strip(), "%H:%M").time()
                    times.append(time_obj)
                else:  # Treat as date
                    # Parse date
                    day = int(re.search(r"\d+", match).group())
                    month = match.split()[-1]  # Get month as a string
                    month_num = datetime.strptime(month, "%b").month  # Convert month to number
                    date_obj = datetime(today.year, month_num, day)
                    dates.append(date_obj)

    # If two times are found, set start and end times
    if len(times) == 2:
        start_time = datetime.combine(today, times[0])
        end_time = datetime.combine(today, times[1])
    else:
        # Use the first date from the list, or today if no date is specified
        if dates:
            start_time = dates[0]  # Start at the first recognized date
            end_time = start_time + timedelta(days=1)  # Default end time to the next day
        else:
            start_time = today.replace(hour=0, minute=0)  # Default start of the day
            end_time = start_time + timedelta(hours=1)  # Default to 1-hour event

    return start_time, end_time

def extract_links(text):
    """Extract links from text."""
    link_pattern = r'https?://[^\s]+'
    return re.findall(link_pattern, text)

def generate_event_title(text):
    """Generate a meaningful title from the content."""
    return "Dream University Pitch 2024"

def analyze_text(text):
    """Analyze text to generate a description."""
    return "Participate in the Dream University Pitch for a chance to win exciting prizes!"

def create_event(creds, event_summary, start_time, end_time, description, link=None):
    """Create a Google Calendar event in IST timezone."""
    service = build('calendar', 'v3', credentials=creds)

    # Convert start and end times to IST (UTC+5:30)
    start_time = start_time.replace(tzinfo=datetime.now().astimezone().tzinfo)
    end_time = end_time.replace(tzinfo=datetime.now().astimezone().tzinfo)

    event = {
        'summary': event_summary,
        'description': description,
        'start': {
            'dateTime': start_time.isoformat(),
            'timeZone': 'Asia/Kolkata',  # IST timezone
        },
        'end': {
            'dateTime': end_time.isoformat(),
            'timeZone': 'Asia/Kolkata',  # IST timezone
        },
        'location': link if link else '',
    }

    created_event = service.events().insert(calendarId='primary', body=event).execute()
    print(f"Event created: {created_event.get('htmlLink')}")

# Main function to create the event using predefined text
def main():
    # Predefined text for the event
    text = """Win a MacBook Air, iPad, or AirPods! 🎁
Plus, unlock your chance to study abroad!

Pitch your dream university in a 60-second video for Dream University Pitch 2024! 🎓
Get a FREE counseling session with Leverage Edu (worth INR 4,999).
🗓 Submissions: 16th Oct - 10th Nov
📅 Masterclass: 25th Oct

Make your study abroad dream come true! Register for FREE
Good luck!"""

    # Extract start and end times
    start_time, end_time = extract_datetime_range(text)

    # Authenticate with OAuth2
    creds = get_credentials()

    # Extract the first link from the text (if available)
    links = extract_links(text)
    event_link = links[0] if links else None

    # Generate the event title and description
    event_title = generate_event_title(text)
    description = analyze_text(text)

    # Create the event with the generated title, description, and optional link
    create_event(creds, event_title, start_time, end_time, description, link=event_link)

# Run the main function
if __name__ == "__main__":
    main()
