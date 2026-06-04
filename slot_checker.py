import re
import html
from typing import Dict, Optional, Tuple
from urllib.parse import parse_qsl
from pathlib import Path

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

import config
from html_parser import extract_slots
from model import CDCPostHeaders, CDCPostPayload


class SlotChecker:
    """Handles HTTP POST requests to CDC booking endpoint and response parsing."""
    
    def __init__(self):
        self.session = self._create_session()
        self.payload = self._parse_post_payload(config.POST_PAYLOAD)

    @staticmethod
    def _save_post_response(response_text: str) -> None:
        """Persist latest raw POST response for quick manual inspection."""
        output_path = Path(config.POST_RESPONSE_DUMP_FILE).expanduser()
        if not output_path.is_absolute():
            output_path = Path.cwd() / output_path
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(response_text, encoding="utf-8")
    
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
        
        # Set cookies from .env COOKIES header
        cookies = self._parse_cookie_header(config.COOKIES)
        for name, value in cookies.items():
            session.cookies.set(name, value)
        
        return session
    
    @staticmethod
    def _parse_cookie_header(raw: str) -> Dict[str, str]:
        text = (raw or "").strip()
        if not text:
            raise RuntimeError("Missing COOKIES in .env")

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
            raise RuntimeError("COOKIES is not a valid cookie header string")
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
        return parsed

    @staticmethod
    def _extract_hidden_field(page_html: str, field_name: str) -> str:
        pattern = rf'name=["\']{re.escape(field_name)}["\'][^>]*value=["\']([^"\']*)["\']'
        match = re.search(pattern, page_html, flags=re.IGNORECASE)
        if not match:
            return ""
        return html.unescape(match.group(1))

    def _fetch_preflight_page_html(self) -> str:
        get_headers = {
            "User-Agent": config.CDC_USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://bookingportal.cdc.com.sg/",
        }
        response = self.session.get(config.CDC_BOOKING_URL, headers=get_headers, timeout=15)
        if response.status_code == 429:
            raise RuntimeError("Rate limited (429) during preflight GET. Refresh COOKIES and retry.")
        response.raise_for_status()
        return response.text

    def _fetch_fresh_hidden_fields(self, page_html: str) -> Dict[str, str]:
        fields = {
            "__VIEWSTATE": self._extract_hidden_field(page_html, "__VIEWSTATE"),
            "__VIEWSTATEGENERATOR": self._extract_hidden_field(page_html, "__VIEWSTATEGENERATOR"),
            "__PREVIOUSPAGE": self._extract_hidden_field(page_html, "__PREVIOUSPAGE"),
            "__EVENTVALIDATION": self._extract_hidden_field(page_html, "__EVENTVALIDATION"),
        }
        missing = [k for k, v in fields.items() if not v]
        if missing:
            raise RuntimeError(
                "Could not extract fresh hidden fields from GET: " + ", ".join(missing)
            )
        return fields

    @staticmethod
    def _resolve_exact_course_value(page_html: str, desired_course_code: str) -> Optional[str]:
        """Find exact dropdown option value for a course code, preserving server spaces."""
        if not desired_course_code:
            return None

        options = re.findall(r'<option[^>]*value="([^"]*)"[^>]*>', page_html, flags=re.IGNORECASE)
        desired = desired_course_code.strip().upper()
        for option_value in options:
            if option_value.strip().upper() == desired:
                return option_value
        return None

    def _apply_fresh_hidden_fields(self, payload: CDCPostPayload) -> CDCPostPayload:
        page_html = self._fetch_preflight_page_html()
        fresh_fields = self._fetch_fresh_hidden_fields(page_html)
        merged = dict(payload)
        merged.update(fresh_fields)

        # If COURSE_CODE is provided, map it to exact server-rendered option value.
        exact_course_value = self._resolve_exact_course_value(page_html, config.COURSE_CODE)
        if exact_course_value is not None:
            merged["ctl00$ContentPlaceHolder1$ddlCourse"] = exact_course_value
        return merged
    
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
            payload = self._apply_fresh_hidden_fields(payload)
            
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
                return 0, "Rate limited (429) by CDC/Cloudflare. Refresh COOKIES and POST_PAYLOAD, then retry."
            
            response.raise_for_status()

            # Always dump response so parser behavior can be verified quickly.
            self._save_post_response(response.text)

            if "|error|500|" in response.text:
                if "Invalid postback or callback argument" in response.text:
                    return 0, "Invalid postback/event validation. Refreshed hidden fields still rejected; refresh COOKIES and POST_PAYLOAD from latest successful request."
                return 0, "CDC returned ASP.NET AJAX error payload (|error|500|). See debug dump file."
            
            # Check for session expiry indicators
            if "session has expired" in response.text.lower() or "not authenticated" in response.text.lower():
                return 0, "Session expired"
            
            # Parse response for slot availability
            response_text = response.text

            slots = extract_slots(response_text)
            available_slots = [slot for slot in slots if slot.is_available]
            if available_slots:
                return len(available_slots), None
            
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
