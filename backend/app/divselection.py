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
from typing import Optional

from playwright.async_api import async_playwright, Page, Browser, ElementHandle


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
            "input:not([type='hidden']):not([type='submit']):not([type='button'])",
            "textarea",
            "select",
            "[contenteditable='true']",
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

    async def analyze_application_page(self, url: str) -> dict:
        """
        Complete workflow: navigate, find fields, highlight, and screenshot.

        Args:
            url: The application page URL

        Returns:
            Dictionary with detected fields and screenshot path
        """
        print(f"Navigating to: {url}")
        await self.navigate(url)

        print("Finding form fields...")
        fields = await self.find_fields()
        print(f"Found {len(fields)} form fields")

        print("Highlighting fields...")
        await self.highlight_fields(fields)

        print("Taking screenshot...")
        screenshot_path = await self.take_screenshot()
        print(f"Screenshot saved to: {screenshot_path}")

        return {
            "url": url,
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
        return await selector.analyze_application_page(url)


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


# Example usage and CLI
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python divselection.py <url>")
        print("Example: python divselection.py https://jobs.example.com/apply")
        sys.exit(1)

    target_url = sys.argv[1]
    headless_mode = "--visible" not in sys.argv

    print(f"Analyzing: {target_url}")
    print(f"Headless mode: {headless_mode}")
    print("-" * 50)

    result = run_analysis(target_url, headless=headless_mode)

    print("\n" + "=" * 50)
    print("ANALYSIS RESULTS")
    print("=" * 50)
    print(f"URL: {result['url']}")
    print(f"Total fields found: {result['field_count']}")
    print(f"Screenshot saved to: {result['screenshot_path']}")
    print("\nField Summary:")
    for field_type, count in result['field_summary'].items():
        print(f"  - {field_type}: {count}")

    print("\nDetailed Fields:")
    for i, field_info in enumerate(result['fields'], 1):
        print(f"  {i}. [{field_info['field_type']}] {field_info['label'] or field_info['name'] or field_info['placeholder'] or 'Unnamed'}")
