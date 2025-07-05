"""
Website Designer - TFrameX Advanced Example

This example demonstrates a sophisticated website generation system using
multiple specialized agents working together to create complete web experiences.

Features:
- Content planning and strategy
- HTML structure generation
- CSS styling with modern frameworks
- Multi-page website coordination
- Asset management and optimization

Author: TFrameX Team
License: MIT
"""

import asyncio
import logging
import os
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv

from tframex import (
    DiscussionPattern,
    Flow,
    InMemoryMemoryStore,
    Message,
    OpenAIChatLLM,
    ParallelPattern,
    RouterPattern,
    SequentialPattern,
    TFrameXApp,
    TFrameXRuntimeContext,
)

# --- Environment and Logging Setup ---
load_dotenv()
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - [%(funcName)s] - %(message)s",
)
logging.getLogger("tframex").setLevel(logging.INFO)
logging.getLogger("tframex.agents.llm_agent").setLevel(logging.DEBUG)

logger = logging.getLogger("website_designer")

# --- LLM Configurations ---
default_llm_config = OpenAIChatLLM(
    model_name=os.getenv("OPENAI_MODEL_NAME", "gpt-3.5-turbo"),
    api_base_url=os.getenv("OPENAI_API_BASE", "http://localhost:11434/v1"),
    api_key=os.getenv("OPENAI_API_KEY", "ollama"),
)

if not default_llm_config.api_base_url:
    logger.error("Error: OPENAI_API_BASE not set for default LLM.")
    exit(1)

# --- Initialize TFrameX Application ---
app = TFrameXApp(default_llm=default_llm_config)


# --- Tools Definition ---
@app.tool(description="Writes content to a file in the website directory.")
async def write_file(file_path: str, content: str) -> str:
    """Write content to a file, creating directories if needed."""
    try:
        # Ensure the directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        
        logger.info(f"File written successfully: {file_path}")
        return f"File written successfully: {file_path}"
    except Exception as e:
        error_msg = f"Error writing file {file_path}: {str(e)}"
        logger.error(error_msg)
        return error_msg


@app.tool(description="Reads content from an existing file.")
async def read_file(file_path: str) -> str:
    """Read content from an existing file."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        logger.info(f"File read successfully: {file_path}")
        return content
    except FileNotFoundError:
        error_msg = f"File not found: {file_path}"
        logger.warning(error_msg)
        return error_msg
    except Exception as e:
        error_msg = f"Error reading file {file_path}: {str(e)}"
        logger.error(error_msg)
        return error_msg


@app.tool(description="Lists files in a directory.")
async def list_files(directory_path: str = ".") -> str:
    """List files in the specified directory."""
    try:
        files = os.listdir(directory_path)
        file_list = "\n".join(files)
        logger.info(f"Listed {len(files)} files in {directory_path}")
        return f"Files in {directory_path}:\n{file_list}"
    except Exception as e:
        error_msg = f"Error listing files in {directory_path}: {str(e)}"
        logger.error(error_msg)
        return error_msg


# --- Agent Definitions ---
@app.agent(
    name="ContentStrategist",
    description="Plans website content strategy and structure",
    system_prompt=(
        "You are a Content Strategist for websites. Your role is to:\n"
        "1. Analyze the client's requirements and target audience\n"
        "2. Create a content strategy and site map\n"
        "3. Define the tone, messaging, and content pillars\n"
        "4. Outline content for each page\n"
        "5. Ensure content aligns with business goals\n\n"
        "Provide detailed content plans including:\n"
        "- Site structure and navigation\n"
        "- Content themes and messaging\n"
        "- Target audience considerations\n"
        "- SEO considerations\n"
        "Be strategic and thorough in your planning."
    ),
    tools=["write_file", "read_file"]
)
async def content_strategist():
    pass


@app.agent(
    name="HTMLDeveloper",
    description="Creates semantic HTML structure and content",
    system_prompt=(
        "You are an expert HTML Developer. Your role is to:\n"
        "1. Create semantic, accessible HTML structures\n"
        "2. Implement proper HTML5 elements and attributes\n"
        "3. Ensure cross-browser compatibility\n"
        "4. Follow web accessibility (WCAG) guidelines\n"
        "5. Create clean, maintainable code\n\n"
        "When creating HTML:\n"
        "- Use semantic elements (header, nav, main, section, article, aside, footer)\n"
        "- Include proper meta tags and SEO elements\n"
        "- Ensure mobile-first responsive structure\n"
        "- Add accessibility attributes (alt text, ARIA labels, etc.)\n"
        "- Use meaningful class names and IDs\n"
        "Create complete, valid HTML documents."
    ),
    tools=["write_file", "read_file", "list_files"]
)
async def html_developer():
    pass


@app.agent(
    name="CSSDesigner",
    description="Creates modern, responsive CSS styling",
    system_prompt=(
        "You are a CSS Designer specializing in modern web design. Your role is to:\n"
        "1. Create beautiful, responsive CSS designs\n"
        "2. Implement modern CSS techniques (Grid, Flexbox, Custom Properties)\n"
        "3. Ensure mobile-first responsive design\n"
        "4. Create consistent design systems\n"
        "5. Optimize for performance and maintainability\n\n"
        "When creating CSS:\n"
        "- Use CSS Grid and Flexbox for layouts\n"
        "- Implement CSS custom properties for theming\n"
        "- Follow BEM or similar naming conventions\n"
        "- Create smooth animations and transitions\n"
        "- Ensure excellent mobile experience\n"
        "- Use modern CSS features appropriately\n"
        "You can use CSS frameworks like Tailwind CSS if appropriate."
    ),
    tools=["write_file", "read_file", "list_files"]
)
async def css_designer():
    pass


@app.agent(
    name="UIUXDesigner",
    description="Focuses on user experience and interface design",
    system_prompt=(
        "You are a UI/UX Designer with expertise in web interfaces. Your role is to:\n"
        "1. Design intuitive user interfaces\n"
        "2. Create excellent user experiences\n"
        "3. Ensure accessibility and usability\n"
        "4. Design consistent visual hierarchies\n"
        "5. Optimize for conversion and engagement\n\n"
        "Consider:\n"
        "- User journey and flow\n"
        "- Information architecture\n"
        "- Visual hierarchy and typography\n"
        "- Color psychology and accessibility\n"
        "- Interactive elements and micro-interactions\n"
        "- Mobile-first design principles\n"
        "Provide detailed design specifications and recommendations."
    ),
    tools=["write_file", "read_file"]
)
async def uiux_designer():
    pass


@app.agent(
    name="WebsiteCoordinator",
    description="Coordinates the entire website creation process",
    system_prompt=(
        "You are the Website Coordinator managing the entire web development project. Your role is to:\n"
        "1. Coordinate between all team members\n"
        "2. Ensure project requirements are met\n"
        "3. Review and approve deliverables\n"
        "4. Manage project timeline and priorities\n"
        "5. Ensure quality and consistency across all pages\n\n"
        "You can call other agents to handle specific tasks:\n"
        "- ContentStrategist for content planning\n"
        "- HTMLDeveloper for HTML structure\n"
        "- CSSDesigner for styling\n"
        "- UIUXDesigner for design guidance\n\n"
        "Always ensure the final website meets all requirements and quality standards."
    ),
    callable_agents=["ContentStrategist", "HTMLDeveloper", "CSSDesigner", "UIUXDesigner"],
    tools=["write_file", "read_file", "list_files"]
)
async def website_coordinator():
    pass


# --- Flow Definitions ---
def create_website_flow() -> Flow:
    """Create the main website generation flow."""
    
    flow = Flow(
        flow_name="WebsiteCreationFlow",
        description="Complete website creation process from strategy to implementation"
    )
    
    # Sequential flow for website creation
    flow.add_step("ContentStrategist")  # Plan content strategy
    flow.add_step(
        ParallelPattern(
            pattern_name="DesignAndDevelopment",
            tasks=["HTMLDeveloper", "CSSDesigner", "UIUXDesigner"]
        )
    )
    flow.add_step("WebsiteCoordinator")  # Final coordination and review
    
    return flow


# --- Main Functions ---
async def create_website_interactive():
    """Interactive website creation with user input."""
    
    print("\n🌐 Welcome to TFrameX Website Designer!")
    print("=====================================")
    
    # Get project requirements
    project_name = input("Enter project name: ").strip()
    website_type = input("Enter website type (business/portfolio/blog/ecommerce): ").strip()
    target_audience = input("Describe target audience: ").strip()
    
    requirements = f"""
    Project: {project_name}
    Type: {website_type}
    Target Audience: {target_audience}
    
    Please create a complete website including:
    - Home page with engaging content
    - About page with company/personal information
    - Contact page with contact form
    - Additional relevant pages based on type
    
    Ensure the website is:
    - Mobile-responsive
    - Accessible (WCAG compliant)
    - SEO optimized
    - Visually appealing
    - Fast loading
    """
    
    logger.info(f"Starting website creation for: {project_name}")
    
    async with app.run_context() as rt:
        # Register the flow
        website_flow = create_website_flow()
        app.register_flow(website_flow)
        
        # Execute the flow
        initial_message = Message(role="user", content=requirements)
        flow_context = await rt.run_flow("WebsiteCreationFlow", initial_message)
        
        print(f"\n✅ Website creation completed!")
        print(f"Final result: {flow_context.current_message.content}")
        
        # List created files
        files_result = await rt.call_agent(
            "WebsiteCoordinator",
            Message(role="user", content="Please list all the files that were created for this website.")
        )
        print(f"\n📁 Created files:\n{files_result.content}")


async def create_website_automated():
    """Automated website creation with predefined requirements."""
    
    requirements = """
    Create a modern business website for "Brew Haven Coffee Shop" with the following specifications:
    
    Project: Brew Haven Coffee Shop Website
    Type: Business/Restaurant website
    Target Audience: Coffee enthusiasts, local community, remote workers
    
    Required pages:
    1. Home page - Welcome, hero section, featured products
    2. About page - Company story, mission, team
    3. Menu page - Coffee drinks, pastries, pricing
    4. Contact page - Location, hours, contact form
    
    Design requirements:
    - Warm, inviting color scheme (browns, oranges, creams)
    - Mobile-responsive design
    - Modern, clean layout
    - Call-to-action buttons
    - Social media integration placeholders
    - SEO optimized
    - Accessibility compliant
    
    Technical requirements:
    - Semantic HTML5
    - Modern CSS (Grid/Flexbox)
    - Responsive images
    - Fast loading times
    """
    
    logger.info("Starting automated website creation for Brew Haven Coffee Shop")
    
    async with app.run_context() as rt:
        # Register the flow
        website_flow = create_website_flow()
        app.register_flow(website_flow)
        
        # Execute the flow
        initial_message = Message(role="user", content=requirements)
        flow_context = await rt.run_flow("WebsiteCreationFlow", initial_message)
        
        print(f"\n✅ Automated website creation completed!")
        print(f"Final result: {flow_context.current_message.content}")


async def main():
    """Main application entry point."""
    
    print("\nTFrameX Website Designer")
    print("========================")
    print("1. Interactive website creation")
    print("2. Automated demo (Brew Haven Coffee Shop)")
    print("3. Chat with Website Coordinator")
    
    choice = input("\nEnter your choice (1-3): ").strip()
    
    try:
        if choice == "1":
            await create_website_interactive()
        elif choice == "2":
            await create_website_automated()
        elif choice == "3":
            async with app.run_context() as rt:
                await rt.interactive_chat(default_agent_name="WebsiteCoordinator")
        else:
            print("Invalid choice. Running automated demo...")
            await create_website_automated()
            
    except Exception as e:
        logger.error(f"Application error: {e}")
        raise


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Website Designer terminated by user")
    except Exception as e:
        logger.error(f"Unhandled error: {e}")
        exit(1)
    
    logger.info("Website Designer completed successfully!")