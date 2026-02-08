"""
Example usage of the async form filler agent.

This agent:
- Uses bounding boxes from divselection.py (no screenshots)
- Controls mouse and keyboard directly (no HTTP API)
- Works asynchronously
- Defaults to localhost:6767
"""
import asyncio
from app.agents.async_form_filler_agent import AsyncFormFillerAgent


async def main():
    """Example: Fill a form on localhost:6767"""
    
    # Initialize the agent
    agent = AsyncFormFillerAgent()
    
    # Job Application Data - Organized by pages
    # The agent will handle multi-step forms automatically
    form_data = {
        # Page 1 - Personal Information
        "firstname": "John",
        "first name": "John",
        "first": "John",
        "lastname": "Smith",
        "last name": "Smith",
        "last": "Smith",
        "name": "John Smith",
        "full name": "John Smith",
        "email": "john.smith@email.com",
        "phone": "(555) 123-4567",
        "telephone": "(555) 123-4567",
        "mobile": "(555) 123-4567",
        
        # Page 2 - Professional Information
        "position": "Software Engineer",
        "job title": "Software Engineer",
        "title": "Software Engineer",
        "experience years": "5",
        "experience": "5",
        "years": "5",
        "years of experience": "5",
        "current company": "Tech Solutions Inc.",
        "company": "Tech Solutions Inc.",
        "employer": "Tech Solutions Inc.",
        
        # Page 3 - Education
        "education": "Bachelor of Science in Computer Science",
        "degree": "Bachelor of Science in Computer Science",
        "university": "State University",
        "college": "State University",
        "school": "State University",
        "graduation year": "2019",
        "year": "2019",
        "graduated": "2019",
        
        # Page 4 - Cover Letter
        "cover letter": """Dear Hiring Manager,

I am writing to express my strong interest in the Software Engineer position at your company. With over 5 years of experience in software development and a solid foundation in computer science, I am confident that I would be a valuable addition to your team.

During my time at Tech Solutions Inc., I have developed expertise in full-stack development, working with modern technologies and frameworks. I have successfully led multiple projects from conception to deployment, collaborating with cross-functional teams to deliver high-quality software solutions.

I am particularly drawn to this opportunity because of your company's commitment to innovation and excellence. I am excited about the possibility of contributing to your team and helping drive your technology initiatives forward.

Thank you for considering my application. I look forward to the opportunity to discuss how my skills and experience align with your needs.

Sincerely,
John Smith""",
        "coverletter": """Dear Hiring Manager,

I am writing to express my strong interest in the Software Engineer position at your company. With over 5 years of experience in software development and a solid foundation in computer science, I am confident that I would be a valuable addition to your team.

During my time at Tech Solutions Inc., I have developed expertise in full-stack development, working with modern technologies and frameworks. I have successfully led multiple projects from conception to deployment, collaborating with cross-functional teams to deliver high-quality software solutions.

I am particularly drawn to this opportunity because of your company's commitment to innovation and excellence. I am excited about the possibility of contributing to your team and helping drive your technology initiatives forward.

Thank you for considering my application. I look forward to the opportunity to discuss how my skills and experience align with your needs.

Sincerely,
John Smith""",
    }
    
    # Fill the form (defaults to localhost:6767)
    result = await agent.fill_form_from_url(
        url="http://localhost:6767",
        data=form_data,
        delay_between_fields=0.3,
        headless=True,  # Set to False to see the browser
    )
    
    print("Form fill result:")
    print(f"Success: {result['success']}")
    print(f"Filled fields: {result['filled_fields']}")
    print(f"Failed fields: {result['failed_fields']}")
    if result['errors']:
        print(f"Errors: {result['errors']}")


if __name__ == "__main__":
    print("⚠️  WARNING: This will control your mouse and keyboard!")
    print("Make sure the form is visible on localhost:6767")
    print("Press Ctrl+C to cancel, or wait 5 seconds to continue...")
    
    try:
        import time
        time.sleep(5)
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nCancelled.")

