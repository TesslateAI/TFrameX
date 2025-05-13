import asyncio
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from dotenv import find_dotenv, load_dotenv

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
load_dotenv(override=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - [%(funcName)s] - %(message)s",
)
logging.getLogger("tframex").setLevel(logging.INFO)
# For more detailed logs:
logging.getLogger("tframex.agents.llm_agent").setLevel(logging.DEBUG)
# logging.getLogger("tframex.agents.base").setLevel(logging.DEBUG)
# logging.getLogger("tframex.app").setLevel(logging.DEBUG)

# --- LLM Configurations ---
# Default LLM (e.g., a local, faster model for general tasks)
default_llm_config = OpenAIChatLLM(
    model_name=os.getenv("OPENAI_MODEL_NAME", "gpt-3.5-turbo"),  # Your default model
    api_base_url=os.getenv("OPENAI_API_BASE", "http://localhost:11434"),
    api_key=os.getenv("OPENAI_API_KEY", "ollama"),
    default_max_tokens=16384,
    timeout=300,  # 5 minutes timeout
)

if not default_llm_config.api_base_url:
    print("Error: OPENAI_API_BASE not set for default LLM.")
    exit(1)

# --- Initialize TFrameX Application ---
app = TFrameXApp(default_llm=default_llm_config)


@app.tool(description="Writes file to file system.")
async def write_file(file_path: str, content: str):
    """Writes file to file system."""

    if file_path.startswith("/"):
        file_path = file_path[1:]

    # Ensure parent directory exists
    parent_dir = os.path.dirname(file_path)
    if parent_dir:  # Check if parent_dir is not an empty string
        if not os.path.exists(parent_dir):
            os.makedirs(parent_dir, exist_ok=True)  # exist_ok=True is safer

    with open(file_path, "w") as f:
        f.write(content)
    logging.info(f"Successfully wrote file: {file_path}")
    return f"Successfully wrote file: {file_path}"


# --- Frontend Generation Agents ---
@app.agent(
    name="frontend_analyzer",
    description="Analyzes user requirements for a multipage web application and generates a detailed plan for HTML and Tailwind CSS implementation.",
    system_prompt="""You are an expert Frontend Requirements Analyzer. Your primary role is to take a user's request for a web application and produce a detailed, structured plan for its creation using HTML and Tailwind CSS. You specialize in multipage applications.

Your tasks are:
1.  **Analyze User Request**: Carefully understand the user's description of the web application they want.
2.  **Identify Pages**: Determine all the distinct HTML pages required for the application (e.g., Home, About, Services, Contact, Product Details).
3.  **Define Page Structure**: For each identified page, list the key sections that should be present (e.g., Header, Navigation, Hero Section, Main Content, Sidebar, Footer).
4.  **Specify Styling Approach**: Mandate the use of Tailwind CSS for all styling.
5.  **Enforce Relative Paths**: State clearly that all internal navigation links between pages must use relative paths (e.g., `./about.html`, `../styles/main.css`).
6.  **Output Format**: Respond ONLY with a single JSON object. Do not include any explanatory text before or after the JSON.

The JSON object must follow this structure:
{
  "application_description": "A brief summary of the web application to be built, based on the user's request.",
  "pages": [
    {
      "file_path": "index.html", // e.g., "index.html", "about.html", "products/product1.html"
      "title": "Homepage",       // Page title for the <title> tag
      "description": "Brief description of this page's purpose and content.",
      "sections": [              // List of main sections for this page
        "Header (with navigation)",
        "Hero Section",
        "Key Features",
        "Footer"
      ]
    }
    // ... more page objects can be included here following the same structure
  ],
  "global_styling": {
    "framework": "Tailwind CSS",
    "notes": [
      "Use Tailwind CSS classes for all styling aspects.",
      "Ensure the design is responsive across common screen sizes (mobile, tablet, desktop) using Tailwind's responsive prefixes.",
      "All internal links between pages of this application MUST use relative paths.",
      "Each HTML page should include the Tailwind CSS CDN link in the <head>: <script src='https://cdn.tailwindcss.com'></script>.",
      "Use semantic HTML5 elements where appropriate."
    ]
  }
}

**Important**: Do NOT generate any HTML code yourself. Your sole output is the JSON plan.
""",
)
async def frontend_analyzer():
    """Analyzes user requirements and creates a structured plan for frontend generation."""
    pass


@app.agent(
    name="frontend_generator",
    description="Generates HTML code for multiple pages using Tailwind CSS, based on a structured plan.",
    system_prompt="""You are an expert HTML and Tailwind CSS Code Generator.
You will receive a JSON plan detailing a multipage web application. Your task is to generate the complete HTML code for each page specified in the plan.

**Input Format:**
You will receive a JSON object from the 'frontend_analyzer' with a structure similar to this:
```json
{
  "application_description": "A simple two-page website about a fictional company.",
  "pages": [
    {
      "file_path": "index.html",
      "title": "Welcome to MyApp",
      "description": "The main landing page for MyApp.",
      "sections": ["Header (with navigation: Home, About)", "Hero Section: Welcome to MyApp", "Main Content: Brief intro", "Footer"]
    },
    {
      "file_path": "about.html",
      "title": "About MyApp",
      "description": "Information about the fictional MyApp company.",
      "sections": ["Header (with navigation: Home, About)", "Main Content: About Us details", "Footer"]
    }
  ],
  "global_styling": {
    "framework": "Tailwind CSS",
    "notes": [
      "Use Tailwind CSS classes for all styling aspects.",
      "Ensure the design is responsive across common screen sizes.",
      "All internal links between pages MUST use relative paths.",
      "Each HTML page should include the Tailwind CSS CDN: <script src='https://cdn.tailwindcss.com'></script>.",
      "Use semantic HTML5 elements."
    ]
  }
}
```

**Your Responsibilities:**

1.  **Iterate Through Pages**: For each page object in the `"pages"` array of the input JSON:
    *   Generate a complete, standalone HTML document.
    *   Use the `file_path` from the page object for the `<file path="...">` wrapper.
    *   Use the `title` from the page object for the HTML `<title>` tag.
    *   Implement all `sections` listed for that page. Be creative and fill them with plausible placeholder content and structure.
2.  **HTML Structure**: Each HTML file must:
    *   Start with `<!DOCTYPE html>`.
    *   Include `<html lang="en">`, `<head>`, and `<body>` tags.
    *   Inside `<head>`:
        *   `<meta charset="UTF-8">`
        *   `<meta name="viewport" content="width=device-width, initial-scale=1.0">`
        *   The correct page `<title>`.
        *   The Tailwind CSS CDN link: `<script src="https://cdn.tailwindcss.com"></script>`.
3.  **Tailwind CSS**:
    *   Style ALL elements using Tailwind CSS classes directly in the HTML.
    *   Implement responsive design using Tailwind's breakpoint prefixes (e.g., `sm:`, `md:`, `lg:`).
    *   Create visually appealing layouts.
4.  **Relative Paths**:
    *   Crucially, all links (`<a>` tags) navigating between the pages of this application **MUST use relative paths** based on their `file_path` values. For example, if you are on `index.html` and linking to `about.html`, the link should be `<a href="./about.html">...</a>`. If on `pages/info.html` linking to `contact.html` (at root), it might be `<a href="../contact.html">...</a>`.
5.  **Content**:
    *   Generate plausible placeholder content for each section. For example, a navigation bar should have links, a hero section some catchy text, etc.
    *   Use semantic HTML5 elements (`<header>`, `<nav>`, `<main>`, `<article>`, `<section>`, `<footer>`, etc.).
6.  **Output Format**:
    *   For EACH page, wrap its complete HTML code within `<file path="THE_ACTUAL_FILE_PATH.html">` and `</file>` tags.
    *   Replace `THE_ACTUAL_FILE_PATH.html` with the `file_path` specified in the input JSON for that page (e.g., `index.html`, `pages/about.html`).
    *   Your entire response MUST consist of these `<file>` blocks, one after another.
    *   **Do NOT include any other text, explanations, or markdown formatting (like ```html) outside of the `<file>...</file>` blocks.**

**Example of a single file output block (your response might contain multiple such blocks):**
<file path="index.html">
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <script src="https://cdn.tailwindcss.com"></script>
    <title>Homepage</title>
</head>
<body class="bg-gray-100 font-sans">
    <header class="bg-blue-600 text-white p-4">
        <nav class="container mx-auto flex justify-between items-center">
            <h1 class="text-xl font-bold">MyApp</h1>
            <div>
                <a href="./index.html" class="px-3 hover:text-blue-200">Home</a>
                <a href="./about.html" class="px-3 hover:text-blue-200">About Us</a>
            </div>
        </nav>
    </header>
    <main class="container mx-auto py-8 px-4">
        <section class="text-center py-12">
            <h2 class="text-4xl font-bold mb-4">Welcome to Our Awesome Website!</h2>
            <p class="text-lg text-gray-700">This is a hero section for the homepage.</p>
        </section>
    </main>
    <footer class="bg-gray-800 text-white text-center p-6 mt-10">
        <p>&copy; 2024 MyApp. All rights reserved.</p>
    </footer>
</body>
</html>
</file>
Ensure your output strictly adheres to this format.
""",
)
async def frontend_generator():
    """Generates frontend code based on the analysis."""
    pass


@app.agent(
    name="file_writer",
    description="Parses input containing multiple file definitions and writes them to the file system using the 'write_file' tool.",
    system_prompt="""Process the input string, which contains one or more file definitions using the format:
`<file path="path/to/your/file.ext">FILE_CONTENT_GOES_HERE</file>`

For **each** `<file ...>` block found:
1.  Extract the `path` attribute value.
2.  Extract the content between the opening and closing `<file>` tags.
3.  Call the `write_file` tool with the extracted `file_path` and `content`.

Your response must **only** contain the necessary `write_file` tool calls. If the input contains multiple `<file>` blocks, make a separate tool call for each.

If no valid `<file ...>` blocks are found, respond with: "No files found to write."

**Do not include any other text or explanations in your response.**
""",
    tools=["write_file"],
)
async def file_writer():
    """Writes the generated code to files."""
    pass


# Create the frontend generation flow
frontend_flow = Flow(
    flow_name="frontend_generation",
    description="Generates a complete frontend implementation based on user requirements.",
)

# Add the sequential pattern for the main flow
frontend_flow.add_step(
    SequentialPattern(
        pattern_name="frontend_generation_sequence",
        steps=["frontend_analyzer", "frontend_generator", "file_writer"],
    )
)

# Register the flow with the app
app.register_flow(frontend_flow)


async def main():
    async with app.run_context(llm_override=None) as rt:
        # To test the flow, you can use interactive chat and ask for a website.
        # For example: "Create a simple two-page website for a coffee shop.
        # It should have a homepage with a welcome message and specials,
        # and an about page with our story. Use Tailwind CSS."
        await rt.interactive_chat()


if __name__ == "__main__":
    if not default_llm_config.api_base_url:
        print(
            "FATAL: OPENAI_API_BASE environment variable is not set for the default LLM."
        )
    else:
        asyncio.run(main())
