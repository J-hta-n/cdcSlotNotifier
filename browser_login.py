from playwright.async_api import async_playwright, Browser, Page
import asyncio
import json
from session_storage import SessionStorage
import config


async def capture_initial_view_state(page: Page) -> dict:
    """Extract __VIEWSTATE, __VIEWSTATEGENERATOR, __EVENTVALIDATION, and __PREVIOUSPAGE from page."""
    try:
        view_state = await page.evaluate('() => document.querySelector("[name=__VIEWSTATE"]")?.value || ""')
        view_state_generator = await page.evaluate('() => document.querySelector("[name=__VIEWSTATEGENERATOR"]")?.value || ""')
        event_validation = await page.evaluate('() => document.querySelector("[name=__EVENTVALIDATION"]")?.value || ""')
        previous_page = await page.evaluate('() => document.querySelector("[name=__PREVIOUSPAGE"]")?.value || ""')
        
        return {
            "view_state": view_state or "",
            "view_state_generator": view_state_generator or "",
            "event_validation": event_validation or "",
            "previous_page": previous_page or "",
        }
    except Exception as e:
        print(f"Warning: Could not extract view state: {e}")
        return {
            "view_state": "",
            "view_state_generator": "",
            "event_validation": "",
            "previous_page": "",
        }


async def login_and_capture_session(headless: bool = False):
    """
    Launch a Playwright browser, navigate to CDC login, prompt user to log in manually,
    capture cookies and view state, then save to session storage.
    
    Args:
        headless: If False, shows a visible browser window
    """
    print("\n" + "="*60)
    print("CDC LOGIN - Manual CAPTCHA Resolution Required")
    print("="*60)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=headless)
        context = await browser.new_context()
        page = await context.new_page()
        
        # Navigate to login page
        print(f"\n→ Navigating to CDC login: {config.CDC_LOGIN_URL}")
        await page.goto(config.CDC_LOGIN_URL, wait_until="networkidle")
        
        # Prompt user
        print("\n→ Browser window is open. Please log in with your CDC credentials.")
        print("→ Complete any CAPTCHA verification as required.")
        print("→ Press Enter here once you have successfully logged in...\n")
        input("  > Press Enter to continue: ")
        
        # Give the page a moment to settle after login
        await asyncio.sleep(2)
        
        # Navigate to booking page to capture view state
        print("\n→ Navigating to booking page...")
        try:
            await page.goto(config.CDC_BOOKING_URL, wait_until="networkidle")
        except Exception as e:
            print(f"Warning: Navigation completed with: {e}")
        
        await asyncio.sleep(1)
        
        # Extract cookies
        cookies_raw = await context.cookies()
        cookies = {cookie["name"]: cookie["value"] for cookie in cookies_raw}
        
        print(f"\n✓ Captured {len(cookies)} cookies")
        
        # Extract view state from booking page
        view_state_data = await capture_initial_view_state(page)
        print(f"✓ Captured view state: {len(view_state_data['view_state'])} bytes")
        
        # Save to session storage
        storage = SessionStorage()
        storage.set_cookies(cookies)
        storage.set_view_state(
            view_state_data["view_state"],
            view_state_data["view_state_generator"],
            view_state_data["event_validation"],
            view_state_data["previous_page"]
        )
        
        await context.close()
        await browser.close()
        
        print("\n✓ Session saved successfully!")
        print("="*60)
        print("You can now start the slot checker scheduler.")
        print("="*60 + "\n")
        
        return True


def sync_login_and_capture_session(headless: bool = False):
    """Synchronous wrapper for async login function."""
    return asyncio.run(login_and_capture_session(headless=headless))
