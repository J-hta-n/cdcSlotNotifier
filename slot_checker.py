import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import re
from typing import Tuple, Optional, Dict
from session_storage import SessionStorage
import config


class SlotChecker:
    """Handles HTTP POST requests to CDC booking endpoint and response parsing."""
    
    def __init__(self):
        self.storage = SessionStorage()
        self.session = self._create_session()
    
    def _create_session(self) -> requests.Session:
        """Create a requests session with retry strategy and cookies."""
        session = requests.Session()
        
        # Add retry strategy for resilience
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # Set cookies from storage
        cookies = self.storage.get_cookies()
        for name, value in cookies.items():
            session.cookies.set(name, value)
        
        return session
    
    def _build_payload(self) -> Dict[str, str]:
        """Build the POST payload for course selection and slot check."""
        view_state_data = self.storage.get_view_state()
        
        # Base payload structure based on CDC endpoint requirements
        payload = {
            "ctl00$ContentPlaceHolder1$ScriptManager1": "ctl00$ContentPlaceHolder1$UpdatePanel1|ctl00$ContentPlaceHolder1$ddlCourse",
            "ctl00_Menu1_TreeView1_ExpandState": "eennnnnnnennnnennenneunnnnnnnnnnnnnnnenen",
            "ctl00_Menu1_TreeView1_SelectedNode": "",
            "__EVENTTARGET": "ctl00$ContentPlaceHolder1$ddlCourse",
            "__EVENTARGUMENT": "",
            "ctl00_Menu1_TreeView1_PopulateLog": "",
            "__LASTFOCUS": "",
            "__VIEWSTATE": view_state_data["view_state"],
            "__VIEWSTATEGENERATOR": view_state_data["view_state_generator"],
            "__PREVIOUSPAGE": view_state_data["previous_page"],
            "__EVENTVALIDATION": view_state_data["event_validation"],
            "ctl00$ContentPlaceHolder1$txtVerificationCode": "",
            "ctl00$ContentPlaceHolder1$ddlCourse": config.COURSE_CODE,
            "ctl00$ContentPlaceHolder1$hdReserveCnt": "0",
            "ctl00$ContentPlaceHolder1$hdTicketEndDate": "",
            "ctl00$ContentPlaceHolder1$hdM1": "0",
            "ctl00$ContentPlaceHolder1$hdM2": "0",
            "ctl00$ContentPlaceHolder1$hdM3": "0",
            "ctl00$ContentPlaceHolder1$hdCacheBackNav": "5",
            "ctl00$ContentPlaceHolder1$hdCacheForNav": "5",
            "ctl00$ContentPlaceHolder1$hdType": "Class3",
            "ctl00$ContentPlaceHolder1$hdDate": "",
            "ctl00$ContentPlaceHolder1$hdSession": "",
            "ctl00$ContentPlaceHolder1$hdDays": "",
        }
        
        return payload
    
    def _extract_view_state_from_response(self, response_text: str) -> bool:
        """
        Extract updated __VIEWSTATE from ASP.NET response and update storage.
        Returns True if successfully extracted and updated.
        """
        try:
            # ASP.NET AJAX responses contain view state updates in specific format
            # Look for pattern: |hiddenField|__VIEWSTATE|<value>|
            match = re.search(r'\|hiddenField\|__VIEWSTATE\|([^|]+)\|', response_text)
            if match:
                new_view_state = match.group(1)
                # Also try to extract other fields
                gen_match = re.search(r'\|hiddenField\|__VIEWSTATEGENERATOR\|([^|]+)\|', response_text)
                event_match = re.search(r'\|hiddenField\|__EVENTVALIDATION\|([^|]+)\|', response_text)
                
                gen_value = gen_match.group(1) if gen_match else ""
                event_value = event_match.group(1) if event_match else ""
                
                self.storage.set_view_state(new_view_state, gen_value, event_value)
                return True
        except Exception as e:
            print(f"Warning: Error extracting view state: {e}")
        return False
    
    def check_slots(self) -> Tuple[int, Optional[str]]:
        """
        Make HTTP POST request to CDC endpoint to check for available slots.
        
        Returns:
            Tuple of (slot_count, error_message)
            - slot_count: 0 if no slots, >0 if slots found
            - error_message: None if successful, error string if session expired or request failed
        """
        
        # Check session validity first
        if not self.storage.is_session_valid():
            return 0, "Session not valid. Please run /login first."
        
        try:
            payload = self._build_payload()
            
            # Make POST request with standard headers
            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                "Accept": "*/*",
                "Accept-Encoding": "gzip, deflate, br",
                "Content-Type": "application/x-www-form-urlencoded",
                "Origin": "https://bookingportal.cdc.com.sg",
                "Referer": "https://bookingportal.cdc.com.sg/",
                "X-MicrosoftAjax": "Delta=true",
            }
            
            response = self.session.post(
                config.CDC_BOOKING_URL,
                data=payload,
                headers=headers,
                timeout=10
            )
            
            response.raise_for_status()
            
            # Extract and update view state for next request
            self._extract_view_state_from_response(response.text)
            
            # Check for session expiry indicators
            if "session has expired" in response.text.lower() or "not authenticated" in response.text.lower():
                return 0, "Session expired"
            
            # Parse response for slot availability
            response_text = response.text
            
            # Look for "No available slots" message
            if "No available slots" in response_text:
                return 0, None
            
            # Try to extract slot count from response
            # Look for patterns like "X session available" or slot grid presence
            session_match = re.search(r'(\d+)\s+session\s+available', response_text, re.IGNORECASE)
            if session_match:
                slot_count = int(session_match.group(1))
                return slot_count, None
            
            # If response has slot grid HTML, assume slots are available
            if "lblSessionNo" in response_text and "display: none" not in response_text:
                # This is a heuristic - the session availability row is visible
                return 1, None  # Conservative: report at least 1 slot found
            
            # Default: no slots found if we couldn't confirm availability
            return 0, None
        
        except requests.exceptions.RequestException as e:
            return 0, f"Request failed: {str(e)}"
        except Exception as e:
            return 0, f"Unexpected error: {str(e)}"
