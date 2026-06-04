import re
from typing import Dict, Optional, Tuple
from urllib.parse import parse_qsl

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

import config
from model import CDCPostHeaders, CDCPostPayload


class SlotChecker:
    """Handles HTTP POST requests to CDC booking endpoint and response parsing."""
    
    def __init__(self):
        self.session = self._create_session()
        self.payload = self._parse_post_payload(config.POST_PAYLOAD)
    
    def _create_session(self) -> requests.Session:
        """Create a requests session with retry strategy and cookies."""
        session = requests.Session()
        
        # Add retry strategy for resilience
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # Set cookies from .env COOKIE header
        cookies = self._parse_cookie_header(config.COOKIE)
        for name, value in cookies.items():
            session.cookies.set(name, value)
        
        return session
    
    @staticmethod
    def _parse_cookie_header(raw: str) -> Dict[str, str]:
        text = (raw or "").strip()
        if not text:
            raise RuntimeError("Missing COOKIE in .env")

        cookies: Dict[str, str] = {}
        for part in text.split(";"):
            pair = part.strip()
            if not pair or "=" not in pair:
                continue
            name, value = pair.split("=", 1)
            name = name.strip()
            if name:
                cookies[name] = value.strip()

        if not cookies:
            raise RuntimeError("COOKIE is not a valid cookie header string")
        return cookies

    @staticmethod
    def _parse_post_payload(raw: str) -> CDCPostPayload:
        text = (raw or "").strip()
        if not text:
            raise RuntimeError("Missing POST_PAYLOAD in .env")

        parsed: Dict[str, str] = dict(parse_qsl(text, keep_blank_values=True))
        missing = [key for key in config.REQUIRED_POST_PAYLOAD_KEYS if key not in parsed]
        if missing:
            raise RuntimeError(
                "POST_PAYLOAD is missing required keys: " + ", ".join(missing)
            )

        # Course can still be overridden in .env.
        parsed["ctl00$ContentPlaceHolder1$ddlCourse"] = config.COURSE_CODE
        return parsed
    
    def check_slots(self) -> Tuple[int, Optional[str]]:
        """
        Make HTTP POST request to CDC endpoint to check for available slots.
        
        Returns:
            Tuple of (slot_count, error_message)
            - slot_count: 0 if no slots, >0 if slots found
            - error_message: None if successful, error string if session expired or request failed
        """
        
        try:
            payload: CDCPostPayload = dict(self.payload)
            
            # Make POST request with standard headers
            headers: CDCPostHeaders = {
                "User-Agent": config.CDC_USER_AGENT,
                "Accept": "*/*",
                "Accept-Encoding": "gzip, deflate, br",
                "Accept-Language": "en-US,en;q=0.9",
                "Content-Type": "application/x-www-form-urlencoded",
                "Origin": "https://bookingportal.cdc.com.sg",
                "Referer": config.CDC_BOOKING_URL,
                "X-MicrosoftAjax": "Delta=true",
            }
            
            response = self.session.post(
                config.CDC_BOOKING_URL,
                data=payload,
                headers=headers,
                timeout=10
            )

            if response.status_code == 429:
                return 0, "Rate limited (429) by CDC/Cloudflare. Refresh COOKIE and POST_PAYLOAD, then retry."
            
            response.raise_for_status()
            
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
