"""
DivSelection Module - Identifies and highlights relevant form fields on job application websites.

This module uses Playwright to:
1. Navigate to an application website
2. Find relevant input fields (name, email, phone, resume, etc.)
3. Highlight them visually
4. Generate a screenshot with the highlighted fields
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional, List, Dict, Any

from playwright.async_api import async_playwright, Page, Browser, ElementHandle


class SubmissionStatus(Enum):
    """Status of job application submission."""
    NOT_SUBMITTED = "not_submitted"
    SUBMITTED = "submitted"
    ERROR = "error"
    PENDING = "pending"
    CONFIRMATION = "confirmation"
    UNKNOWN = "unknown"


@dataclass
class SubmissionResult:
    """Represents the result of a submission detection analysis."""
    status: SubmissionStatus
    confidence: float  # 0.0 to 1.0
    indicators: List[str]
    confirmation_text: str
    success_elements: List[Dict[str, Any]]
    error_elements: List[Dict[str, Any]]
    screenshot_path: str
    url: str

    def to_dict(self) -> dict:
        return {
            "status": self.status.value,
            "confidence": self.confidence,
            "indicators": self.indicators,
            "confirmation_text": self.confirmation_text,
            "success_elements": self.success_elements,
            "error_elements": self.error_elements,
            "screenshot_path": self.screenshot_path,
            "url": self.url
        }


# Keywords that indicate successful submission
SUCCESS_KEYWORDS = [
    "success", "successful", "submitted", "received", "thank you", "thanks",
    "confirmation", "confirmed", "application submitted", "we have received",
    "your application", "application complete", "submission complete",
    "congratulations", "next steps", "we'll be in touch", "review your application",
    "application id", "reference number", "tracking number", "confirmation number"
]

# Keywords that indicate errors or failures
ERROR_KEYWORDS = [
    "error", "failed", "failure", "problem", "issue", "invalid", "required",
    "missing", "incorrect", "please try again", "something went wrong",
    "unable to submit", "submission failed", "application failed", "expired",
    "session expired", "timeout", "network error", "server error"
]

# Keywords that indicate pending or in-progress status
PENDING_KEYWORDS = [
    "processing", "please wait", "loading", "submitting", "in progress",
    "uploading", "validating", "checking", "reviewing", "pending"
]

# Visual indicators (CSS classes and IDs)
SUCCESS_INDICATORS = [
    "success", "alert-success", "message-success", "notification-success",
    "confirmation", "thank-you", "submitted", "complete"
]

ERROR_INDICATORS = [
    "error", "alert-error", "alert-danger", "message-error", "notification-error",
    "failure", "invalid", "required-field", "validation-error"
]


class FieldType(Enum):
    """Types of form fields commonly found in job applications."""
    TEXT = "text"
    EMAIL = "email"
    PHONE = "phone"
    NAME = "name"
    FILE = "file"
    TEXTAREA = "textarea"
    SELECT = "select"
    CHECKBOX = "checkbox"
    RADIO = "radio"
    URL = "url"
    DATE = "date"
    PASSWORD = "password"
    BUTTON = "button"
    SUBMIT = "submit"
    UNKNOWN = "unknown"


@dataclass
class FormField:
    """Represents a detected form field."""
    element_id: str
    field_type: FieldType
    label: str
    name: str
    placeholder: str
    required: bool
    selector: str
    bounding_box: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "element_id": self.element_id,
            "field_type": self.field_type.value,
            "label": self.label,
            "name": self.name,
            "placeholder": self.placeholder,
            "required": self.required,
            "selector": self.selector,
            "bounding_box": self.bounding_box
        }


# Keywords that indicate relevant job application fields
FIELD_KEYWORDS = {
    FieldType.NAME: ["name", "first", "last", "full", "firstname", "lastname", "fullname"],
    FieldType.EMAIL: ["email", "e-mail", "mail"],
    FieldType.PHONE: ["phone", "tel", "telephone", "mobile", "cell"],
    FieldType.FILE: ["resume", "cv", "upload", "file", "attachment", "document"],
    FieldType.URL: ["linkedin", "portfolio", "website", "github", "url", "link"],
    FieldType.DATE: ["date", "start", "available", "availability"],
    FieldType.SUBMIT: ["submit", "send", "apply", "next", "continue", "proceed", "finish", "complete"],
    FieldType.BUTTON: ["button", "btn", "click", "action"],
}

# Highlight colors for different field types
HIGHLIGHT_COLORS = {
    FieldType.NAME: "#FF6B6B",      # Red
    FieldType.EMAIL: "#4ECDC4",     # Teal
    FieldType.PHONE: "#45B7D1",     # Blue
    FieldType.FILE: "#96CEB4",      # Green
    FieldType.URL: "#FFEAA7",       # Yellow
    FieldType.DATE: "#DDA0DD",      # Plum
    FieldType.TEXT: "#FFB347",      # Orange
    FieldType.TEXTAREA: "#87CEEB",  # Sky Blue
    FieldType.SELECT: "#98D8C8",    # Mint
    FieldType.CHECKBOX: "#F7DC6F",  # Light Yellow
    FieldType.RADIO: "#BB8FCE",     # Light Purple
    FieldType.PASSWORD: "#FF69B4",  # Hot Pink
    FieldType.SUBMIT: "#FF4444",    # Bright Red
    FieldType.BUTTON: "#FF8C00",    # Dark Orange
    FieldType.UNKNOWN: "#BDC3C7",   # Gray
}


class DivSelector:
    """
    Analyzes web pages to find, highlight, and screenshot form fields.
    """

    def __init__(self, headless: bool = True, screenshot_dir: str = "screenshots"):
        """
        Initialize the DivSelector.

        Args:
            headless: Run browser in headless mode
            screenshot_dir: Directory to save screenshots
        """
        self.headless = headless
        self.screenshot_dir = Path(screenshot_dir)
        self.screenshot_dir.mkdir(parents=True, exist_ok=True)
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.detected_fields: list[FormField] = []

    async def __aenter__(self):
        """Async context manager entry."""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    async def start(self):
        """Start the browser."""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=self.headless)
        self.page = await self.browser.new_page()
        # Set a reasonable viewport size
        await self.page.set_viewport_size({"width": 1920, "height": 1080})

    async def close(self):
        """Close the browser and cleanup."""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

    async def navigate(self, url: str, wait_for_load: bool = True):
        """
        Navigate to a URL.

        Args:
            url: The URL to navigate to
            wait_for_load: Wait for the page to fully load
        """
        if not self.page:
            raise RuntimeError("Browser not started. Call start() first.")

        await self.page.goto(url, wait_until="networkidle" if wait_for_load else "domcontentloaded")
        # Give dynamic content time to render
        await asyncio.sleep(1)

    async def load_html(self, html_content: str, base_url: str = "about:blank"):
        """
        Load HTML content directly into the page.

        Args:
            html_content: The HTML content to load
            base_url: Base URL for resolving relative links (optional)
        """
        if not self.page:
            raise RuntimeError("Browser not started. Call start() first.")

        await self.page.goto(base_url)
        await self.page.set_content(html_content, wait_until="domcontentloaded")
        # Give dynamic content time to render
        await asyncio.sleep(1)

    def _classify_field_type(self, input_type: str, attributes: dict) -> FieldType:
        """
        Classify a field based on its type and attributes.

        Args:
            input_type: The input element's type attribute
            attributes: Dictionary of element attributes

        Returns:
            The classified FieldType
        """
        # First check input type
        type_mapping = {
            "email": FieldType.EMAIL,
            "tel": FieldType.PHONE,
            "file": FieldType.FILE,
            "url": FieldType.URL,
            "date": FieldType.DATE,
            "checkbox": FieldType.CHECKBOX,
            "radio": FieldType.RADIO,
            "password": FieldType.PASSWORD,
            "submit": FieldType.SUBMIT,
            "button": FieldType.BUTTON,
        }

        if input_type in type_mapping:
            return type_mapping[input_type]

        # Check attributes for keywords
        searchable = " ".join([
            attributes.get("name", ""),
            attributes.get("id", ""),
            attributes.get("placeholder", ""),
            attributes.get("aria-label", ""),
            attributes.get("class", ""),
        ]).lower()

        for field_type, keywords in FIELD_KEYWORDS.items():
            if any(kw in searchable for kw in keywords):
                return field_type

        if input_type == "text":
            return FieldType.TEXT

        return FieldType.UNKNOWN

    async def _classify_button_type(self, element: ElementHandle, attributes: dict) -> FieldType:
        """
        Classify a button element as either submit or generic button.

        Args:
            element: The button element
            attributes: Dictionary of element attributes

        Returns:
            FieldType.SUBMIT or FieldType.BUTTON
        """
        # Get button text content
        button_text = await element.evaluate("el => el.textContent || el.value || ''")

        # Combine all searchable text
        searchable = " ".join([
            attributes.get("name", ""),
            attributes.get("id", ""),
            attributes.get("class", ""),
            attributes.get("aria-label", ""),
            button_text,
        ]).lower()

        # Check for submit-related keywords
        submit_keywords = FIELD_KEYWORDS[FieldType.SUBMIT]
        if any(kw in searchable for kw in submit_keywords):
            return FieldType.SUBMIT
        # Default to generic button
        return FieldType.BUTTON

    async def _get_element_attributes(self, element: ElementHandle) -> dict:
        """Get relevant attributes from an element."""
        return await element.evaluate("""
            el => ({
                id: el.id || '',
                name: el.name || '',
                type: el.type || '',
                placeholder: el.placeholder || '',
                required: el.required || false,
                'aria-label': el.getAttribute('aria-label') || '',
                class: el.className || '',
                tagName: el.tagName.toLowerCase()
            })
        """)

    async def _find_label_for_element(self, element: ElementHandle) -> str:
        """Find the label text associated with an element."""
        label = await element.evaluate("""
            el => {
                // Check for associated label via 'for' attribute
                if (el.id) {
                    const label = document.querySelector(`label[for="${el.id}"]`);
                    if (label) return label.textContent.trim();
                }
                
                // Check for parent label
                const parentLabel = el.closest('label');
                if (parentLabel) return parentLabel.textContent.trim();
                
                // Check for aria-label
                const ariaLabel = el.getAttribute('aria-label');
                if (ariaLabel) return ariaLabel;
                
                // Check for preceding sibling or parent text
                const parent = el.parentElement;
                if (parent) {
                    const text = parent.textContent.trim();
                    if (text.length < 100) return text;
                }
                
                return '';
            }
        """)
        return label or ""

    async def find_fields(self) -> list[FormField]:
        """
        Find all relevant form fields on the current page.

        Returns:
            List of detected FormField objects
        """
        if not self.page:
            raise RuntimeError("Browser not started. Call start() first.")

        self.detected_fields = []

        # Selectors for common form elements
        selectors = [
            "input:not([type='hidden'])",  # Include all inputs now
            "textarea",
            "select",
            "[contenteditable='true']",
            "button",  # Button elements
            "input[type='submit']",  # Submit inputs
            "input[type='button']",  # Button inputs
        ]

        for selector in selectors:
            elements = await self.page.query_selector_all(selector)

            for i, element in enumerate(elements):
                try:
                    # Check if element is visible
                    is_visible = await element.is_visible()
                    if not is_visible:
                        continue

                    attrs = await self._get_element_attributes(element)

                    # For buttons, prefer text content as label
                    tag_name = attrs.get("tagName", "input")
                    if tag_name == "button" or attrs.get("type") in ["submit", "button"]:
                        button_text = await element.evaluate("el => el.textContent || el.value || ''")
                        label = button_text.strip() or await self._find_label_for_element(element)
                    else:
                        label = await self._find_label_for_element(element)

                    # Get bounding box for the element
                    box = await element.bounding_box()
                    if not box:
                        continue

                    # Determine field type
                    tag_name = attrs.get("tagName", "input")
                    input_type = attrs.get("type", "text")

                    if tag_name == "textarea":
                        field_type = FieldType.TEXTAREA
                    elif tag_name == "select":
                        field_type = FieldType.SELECT
                    elif tag_name == "button":
                        # For button elements, check text content and attributes for submit keywords
                        field_type = await self._classify_button_type(element, attrs)
                    elif input_type in ["submit", "button"]:
                        # For input elements of type submit or button
                        field_type = await self._classify_button_type(element, attrs)
                    else:
                        field_type = self._classify_field_type(input_type, attrs)

                    # Create unique selector for the element
                    element_id = attrs.get("id", "")
                    element_name = attrs.get("name", "")

                    if element_id:
                        unique_selector = f"#{element_id}"
                    elif element_name:
                        unique_selector = f"{tag_name}[name='{element_name}']"
                    else:
                        unique_selector = f"{selector}:nth-of-type({i + 1})"

                    form_field = FormField(
                        element_id=element_id or f"field_{i}",
                        field_type=field_type,
                        label=label,
                        name=element_name,
                        placeholder=attrs.get("placeholder", ""),
                        required=attrs.get("required", False),
                        selector=unique_selector,
                        bounding_box={
                            "x": box["x"],
                            "y": box["y"],
                            "width": box["width"],
                            "height": box["height"]
                        }
                    )

                    self.detected_fields.append(form_field)

                except Exception as e:
                    # Skip elements that can't be processed
                    print(f"Warning: Could not process element: {e}")
                    continue

        return self.detected_fields

    async def highlight_fields(self, fields: Optional[list[FormField]] = None):
        """
        Highlight the detected fields on the page.

        Args:
            fields: List of fields to highlight. Uses detected_fields if None.
        """
        if not self.page:
            raise RuntimeError("Browser not started. Call start() first.")

        fields = fields or self.detected_fields

        if not fields:
            print("No fields to highlight.")
            return

        # Inject highlighting styles and create overlay elements
        for i, form_field in enumerate(fields):
            color = HIGHLIGHT_COLORS.get(form_field.field_type, HIGHLIGHT_COLORS[FieldType.UNKNOWN])
            box = form_field.bounding_box

            if not box:
                continue

            # Create highlight overlay
            await self.page.evaluate(f"""
                (() => {{
                    const overlay = document.createElement('div');
                    overlay.id = 'highlight-overlay-{i}';
                    overlay.style.cssText = `
                        position: absolute;
                        left: {box['x']}px;
                        top: {box['y']}px;
                        width: {box['width']}px;
                        height: {box['height']}px;
                        border: 3px solid {color};
                        background-color: {color}33;
                        pointer-events: none;
                        z-index: 10000;
                        box-sizing: border-box;
                    `;
                    document.body.appendChild(overlay);
                    
                    // Add label badge
                    const badge = document.createElement('div');
                    badge.style.cssText = `
                        position: absolute;
                        left: {box['x']}px;
                        top: {box['y'] - 25}px;
                        background-color: {color};
                        color: #000;
                        padding: 2px 8px;
                        font-size: 12px;
                        font-weight: bold;
                        font-family: Arial, sans-serif;
                        border-radius: 3px;
                        z-index: 10001;
                        white-space: nowrap;
                    `;
                    badge.textContent = '{form_field.field_type.value.upper()}';
                    document.body.appendChild(badge);
                }})();
            """)

    async def take_screenshot(self, filename: Optional[str] = None, full_page: bool = True) -> str:
        """
        Take a screenshot of the current page.

        Args:
            filename: Custom filename. Auto-generated if None.
            full_page: Capture the full page or just the viewport.

        Returns:
            Path to the saved screenshot
        """
        if not self.page:
            raise RuntimeError("Browser not started. Call start() first.")

        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"fields_screenshot_{timestamp}.png"

        screenshot_path = self.screenshot_dir / filename
        await self.page.screenshot(path=str(screenshot_path), full_page=full_page)

        return str(screenshot_path)

    async def analyze_application_page(self, url: str = None, html_content: str = None, base_url: str = "about:blank") -> dict:
        """
        Complete workflow: load content (URL or HTML), find fields, highlight, and screenshot.

        Args:
            url: The application page URL (optional if html_content is provided)
            html_content: HTML content to analyze (optional if url is provided)
            base_url: Base URL for resolving relative links when using html_content

        Returns:
            Dictionary with detected fields and screenshot path
        """
        if not url and not html_content:
            raise ValueError("Either url or html_content must be provided")

        if url and html_content:
            raise ValueError("Only one of url or html_content should be provided")

        if url:
            print(f"Navigating to: {url}")
            await self.navigate(url)
            source = url
        else:
            print(f"Loading HTML content ({len(html_content)} characters)")
            await self.load_html(html_content, base_url)
            source = f"HTML content ({len(html_content)} chars)"

        print("Finding form fields...")
        fields = await self.find_fields()
        print(f"Found {len(fields)} form fields")

        print("Highlighting fields...")
        await self.highlight_fields(fields)

        print("Taking screenshot...")
        screenshot_path = await self.take_screenshot()
        print(f"Screenshot saved to: {screenshot_path}")

        return {
            "source": source,
            "url": url,
            "html_length": len(html_content) if html_content else None,
            "fields": [f.to_dict() for f in fields],
            "field_count": len(fields),
            "screenshot_path": screenshot_path,
            "field_summary": self._get_field_summary(fields)
        }

    def _get_field_summary(self, fields: list[FormField]) -> dict:
        """Generate a summary of field types found."""
        summary = {}
        for form_field in fields:
            field_type = form_field.field_type.value
            summary[field_type] = summary.get(field_type, 0) + 1
        return summary

    async def _extract_element_info(self, element: ElementHandle) -> Dict[str, Any]:
        """Extract information from an element for submission analysis."""
        return await element.evaluate("""
            el => ({
                text: el.textContent.trim(),
                id: el.id || '',
                className: el.className || '',
                tagName: el.tagName.toLowerCase(),
                innerHTML: el.innerHTML,
                visible: el.offsetParent !== null,
                boundingBox: {
                    x: el.getBoundingClientRect().x,
                    y: el.getBoundingClientRect().y,
                    width: el.getBoundingClientRect().width,
                    height: el.getBoundingClientRect().height
                }
            })
        """)

    async def _search_for_keywords(self, keywords: List[str], element_selectors: List[str]) -> List[Dict[str, Any]]:
        """Search for specific keywords in page elements."""
        found_elements = []

        for selector in element_selectors:
            try:
                elements = await self.page.query_selector_all(selector)
                for element in elements:
                    if not await element.is_visible():
                        continue

                    element_info = await self._extract_element_info(element)
                    text_content = element_info['text'].lower()

                    # Check if any keyword is found in the text
                    matching_keywords = [kw for kw in keywords if kw.lower() in text_content]
                    if matching_keywords:
                        element_info['matching_keywords'] = matching_keywords
                        element_info['selector'] = selector
                        found_elements.append(element_info)

            except Exception as e:
                # Continue if selector fails
                continue

        return found_elements

    async def _check_url_indicators(self) -> List[str]:
        """Check URL for submission success indicators."""
        current_url = self.page.url.lower()
        indicators = []

        url_success_patterns = [
            'success', 'submitted', 'confirmation', 'thank-you', 'complete',
            'application-submitted', 'submission-complete', 'thank_you'
        ]

        for pattern in url_success_patterns:
            if pattern in current_url:
                indicators.append(f"URL contains '{pattern}'")

        return indicators

    async def _analyze_page_title(self) -> List[str]:
        """Analyze page title for submission indicators."""
        title = await self.page.title()
        title_lower = title.lower()
        indicators = []

        for keyword in SUCCESS_KEYWORDS:
            if keyword in title_lower:
                indicators.append(f"Page title contains '{keyword}': {title}")

        for keyword in ERROR_KEYWORDS:
            if keyword in title_lower:
                indicators.append(f"Page title contains error '{keyword}': {title}")

        return indicators

    async def detect_submission_status(self) -> SubmissionResult:
        """
        Detect if a job application has been successfully submitted.

        Returns:
            SubmissionResult with detection details
        """
        if not self.page:
            raise RuntimeError("Browser not started. Call start() first.")

        indicators = []
        success_elements = []
        error_elements = []
        confirmation_text = ""

        # Element selectors to search for submission status
        search_selectors = [
            "div", "p", "span", "h1", "h2", "h3", "h4", "h5", "h6",
            ".message", ".alert", ".notification", ".success", ".error",
            ".confirmation", ".status", ".result", "#message", "#alert",
            "#confirmation", "#status", "#result"
        ]

        # Check URL indicators
        url_indicators = await self._check_url_indicators()
        indicators.extend(url_indicators)

        # Check page title
        title_indicators = await self._analyze_page_title()
        indicators.extend(title_indicators)

        # Search for success keywords
        success_elements = await self._search_for_keywords(SUCCESS_KEYWORDS, search_selectors)

        # Search for error keywords
        error_elements = await self._search_for_keywords(ERROR_KEYWORDS, search_selectors)

        # Search for pending keywords
        pending_elements = await self._search_for_keywords(PENDING_KEYWORDS, search_selectors)

        # Check for visual indicators in CSS classes
        visual_success = []
        visual_error = []

        for indicator in SUCCESS_INDICATORS:
            elements = await self.page.query_selector_all(f".{indicator}")
            for element in elements:
                if await element.is_visible():
                    info = await self._extract_element_info(element)
                    info['indicator_type'] = 'css_class'
                    info['indicator_value'] = indicator
                    visual_success.append(info)

        for indicator in ERROR_INDICATORS:
            elements = await self.page.query_selector_all(f".{indicator}")
            for element in elements:
                if await element.is_visible():
                    info = await self._extract_element_info(element)
                    info['indicator_type'] = 'css_class'
                    info['indicator_value'] = indicator
                    visual_error.append(info)

        success_elements.extend(visual_success)
        error_elements.extend(visual_error)

        # Extract confirmation text from success elements
        if success_elements:
            confirmation_text = " | ".join([elem['text'][:200] for elem in success_elements[:3] if elem['text']])

        # Determine status and confidence
        status, confidence = self._determine_status(
            success_elements, error_elements, pending_elements, url_indicators, title_indicators
        )

        # Add specific indicators
        if success_elements:
            indicators.append(f"Found {len(success_elements)} success elements")
        if error_elements:
            indicators.append(f"Found {len(error_elements)} error elements")
        if pending_elements:
            indicators.append(f"Found {len(pending_elements)} pending elements")

        # Take screenshot for documentation
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        screenshot_filename = f"submission_check_{timestamp}.png"
        screenshot_path = await self.take_screenshot(screenshot_filename)

        return SubmissionResult(
            status=status,
            confidence=confidence,
            indicators=indicators,
            confirmation_text=confirmation_text,
            success_elements=success_elements,
            error_elements=error_elements,
            screenshot_path=screenshot_path,
            url=self.page.url
        )

    def _determine_status(self, success_elements: List[Dict], error_elements: List[Dict],
                         pending_elements: List[Dict], url_indicators: List[str],
                         title_indicators: List[str]) -> tuple[SubmissionStatus, float]:
        """Determine submission status and confidence based on found elements."""

        success_score = len(success_elements) * 2 + len(url_indicators) * 3
        error_score = len(error_elements) * 2
        pending_score = len(pending_elements) * 1

        # High confidence thresholds
        if success_score >= 4 and error_score == 0:
            return SubmissionStatus.SUBMITTED, min(0.95, 0.7 + success_score * 0.05)

        if error_score >= 3 and success_score == 0:
            return SubmissionStatus.ERROR, min(0.9, 0.6 + error_score * 0.05)

        if pending_score >= 2 and success_score == 0 and error_score == 0:
            return SubmissionStatus.PENDING, min(0.8, 0.5 + pending_score * 0.1)

        # Medium confidence scenarios
        if success_score >= 2:
            return SubmissionStatus.SUBMITTED, min(0.8, 0.5 + success_score * 0.05)

        if error_score >= 1:
            return SubmissionStatus.ERROR, min(0.7, 0.4 + error_score * 0.1)

        if pending_score >= 1:
            return SubmissionStatus.PENDING, min(0.6, 0.3 + pending_score * 0.1)

        # Check for confirmation patterns in URL
        url_check = any('success' in indicator or 'submitted' in indicator or 'confirmation' in indicator
                       for indicator in url_indicators)
        if url_check:
            return SubmissionStatus.CONFIRMATION, 0.75

        # Default to not submitted if no clear indicators
        return SubmissionStatus.NOT_SUBMITTED, 0.3

    async def analyze_submission_status(self, url: str = None, html_content: str = None,
                                      base_url: str = "about:blank") -> Dict[str, Any]:
        """
        Complete workflow to analyze submission status of a page.

        Args:
            url: The page URL to check (optional if html_content is provided)
            html_content: HTML content to analyze (optional if url is provided)
            base_url: Base URL for resolving relative links when using html_content

        Returns:
            Dictionary with submission status analysis results
        """
        if not url and not html_content:
            raise ValueError("Either url or html_content must be provided")

        if url and html_content:
            raise ValueError("Only one of url or html_content should be provided")

        if url:
            print(f"Navigating to: {url}")
            await self.navigate(url)
            source = url
        else:
            print(f"Loading HTML content ({len(html_content)} characters)")
            await self.load_html(html_content, base_url)
            source = f"HTML content ({len(html_content)} chars)"

        print("Detecting submission status...")
        result = await self.detect_submission_status()

        return {
            "source": source,
            "submission_result": result.to_dict()
        }


async def analyze_url(url: str, headless: bool = True, screenshot_dir: str = "screenshots") -> dict:
    """
    Convenience function to analyze a URL.

    Args:
        url: The application page URL
        headless: Run browser in headless mode
        screenshot_dir: Directory to save screenshots

    Returns:
        Dictionary with analysis results
    """
    async with DivSelector(headless=headless, screenshot_dir=screenshot_dir) as selector:
        return await selector.analyze_application_page(url=url)


async def analyze_html(html_content: str, base_url: str = "about:blank", headless: bool = True, screenshot_dir: str = "screenshots") -> dict:
    """
    Convenience function to analyze HTML content.

    Args:
        html_content: The HTML content to analyze
        base_url: Base URL for resolving relative links
        headless: Run browser in headless mode
        screenshot_dir: Directory to save screenshots

    Returns:
        Dictionary with analysis results
    """
    async with DivSelector(headless=headless, screenshot_dir=screenshot_dir) as selector:
        return await selector.analyze_application_page(html_content=html_content, base_url=base_url)


def run_analysis(url: str, headless: bool = True, screenshot_dir: str = "screenshots") -> dict:
    """
    Synchronous wrapper for analyze_url.

    Args:
        url: The application page URL
        headless: Run browser in headless mode
        screenshot_dir: Directory to save screenshots

    Returns:
        Dictionary with analysis results
    """
    return asyncio.run(analyze_url(url, headless, screenshot_dir))


def run_html_analysis(html_content: str, base_url: str = "about:blank", headless: bool = True, screenshot_dir: str = "screenshots") -> dict:
    """
    Synchronous wrapper for analyze_html.

    Args:
        html_content: The HTML content to analyze
        base_url: Base URL for resolving relative links
        headless: Run browser in headless mode
        screenshot_dir: Directory to save screenshots

    Returns:
        Dictionary with analysis results
    """
    return asyncio.run(analyze_html(html_content, base_url, headless, screenshot_dir))


async def check_submission_status(url: str, headless: bool = True, screenshot_dir: str = "screenshots") -> dict:
    """
    Convenience function to check submission status of a URL.

    Args:
        url: The page URL to check
        headless: Run browser in headless mode
        screenshot_dir: Directory to save screenshots

    Returns:
        Dictionary with submission status analysis results
    """
    async with DivSelector(headless=headless, screenshot_dir=screenshot_dir) as selector:
        return await selector.analyze_submission_status(url=url)


async def check_html_submission_status(html_content: str, base_url: str = "about:blank",
                                     headless: bool = True, screenshot_dir: str = "screenshots") -> dict:
    """
    Convenience function to check submission status of HTML content.

    Args:
        html_content: The HTML content to analyze
        base_url: Base URL for resolving relative links
        headless: Run browser in headless mode
        screenshot_dir: Directory to save screenshots

    Returns:
        Dictionary with submission status analysis results
    """
    async with DivSelector(headless=headless, screenshot_dir=screenshot_dir) as selector:
        return await selector.analyze_submission_status(html_content=html_content, base_url=base_url)


def run_submission_check(url: str, headless: bool = True, screenshot_dir: str = "screenshots") -> dict:
    """
    Synchronous wrapper for check_submission_status.

    Args:
        url: The page URL to check
        headless: Run browser in headless mode
        screenshot_dir: Directory to save screenshots

    Returns:
        Dictionary with submission status analysis results
    """
    return asyncio.run(check_submission_status(url, headless, screenshot_dir))


def run_html_submission_check(html_content: str, base_url: str = "about:blank",
                             headless: bool = True, screenshot_dir: str = "screenshots") -> dict:
    """
    Synchronous wrapper for check_html_submission_status.

    Args:
        html_content: The HTML content to analyze
        base_url: Base URL for resolving relative links
        headless: Run browser in headless mode
        screenshot_dir: Directory to save screenshots

    Returns:
        Dictionary with submission status analysis results
    """
    return asyncio.run(check_html_submission_status(html_content, base_url, headless, screenshot_dir))


# Example usage and CLI
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage:")
        print("  URL analysis:  python divselection.py <url>")
        print("  HTML analysis: python divselection.py --html <html_file_path>")
        print("Examples:")
        print("  python divselection.py https://jobs.example.com/apply")
        print("  python divselection.py --html application_form.html")
        print("Options:")
        print("  --visible: Run browser in visible mode (default: headless)")
        sys.exit(1)

    headless_mode = "--visible" not in sys.argv

    if "--html" in sys.argv:
        # HTML file analysis
        html_file_path = None
        try:
            html_file_index = sys.argv.index("--html") + 1
            if html_file_index >= len(sys.argv):
                print("Error: No HTML file path provided after --html")
                sys.exit(1)

            html_file_path = sys.argv[html_file_index]

            with open(html_file_path, 'r', encoding='utf-8') as f:
                html_content = f.read()

            print(f"Analyzing HTML file: {html_file_path}")
            print(f"HTML content length: {len(html_content)} characters")
            print(f"Headless mode: {headless_mode}")
            print("-" * 50)

            result = run_html_analysis(html_content, headless=headless_mode)

        except FileNotFoundError:
            print(f"Error: HTML file '{html_file_path or 'unknown'}' not found")
            sys.exit(1)
        except Exception as e:
            print(f"Error reading HTML file: {e}")
            sys.exit(1)
    else:
        # URL analysis
        target_url = sys.argv[1]

        print(f"Analyzing URL: {target_url}")
        print(f"Headless mode: {headless_mode}")
        print("-" * 50)

        result = run_analysis(target_url, headless=headless_mode)

    print("\n" + "=" * 50)
    print("ANALYSIS RESULTS")
    print("=" * 50)
    print(f"Source: {result['source']}")
    if result.get('url'):
        print(f"URL: {result['url']}")
    if result.get('html_length'):
        print(f"HTML content length: {result['html_length']} characters")
    print(f"Total fields found: {result['field_count']}")
    print(f"Screenshot saved to: {result['screenshot_path']}")
    print("\nField Summary:")
    for field_type, count in result['field_summary'].items():
        print(f"  - {field_type}: {count}")

    print("\nDetailed Fields:")
    for i, field_info in enumerate(result['fields'], 1):
        print(f"  {i}. [{field_info['field_type']}] {field_info['label'] or field_info['name'] or field_info['placeholder'] or 'Unnamed'}")
