import asyncio
import logging
import os

from dotenv import load_dotenv

from tframex import Flow, OpenAIChatLLM, SequentialPattern, TFrameXApp
from tframex.patterns.delegate_pattern import DelegatePattern, ProcessingMode

# --- Environment and Logging Setup ---
load_dotenv(override=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - [%(funcName)s] - %(message)s",
)
logging.getLogger("tframex").setLevel(logging.INFO)
# For more detailed logs:
logging.getLogger("tframex.agents.llm_agent").setLevel(logging.DEBUG)
logging.getLogger("llm_interaction").setLevel(logging.DEBUG)

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
    description="Analyzes user requirements for a multipage web application and generates a detailed plan with shared context and individual page tasks.",
    system_prompt="""You are an expert Frontend Requirements Analyzer. Your primary role is to take a user's request for a web application and produce a detailed, structured plan for its creation using HTML and Tailwind CSS. You specialize in multipage applications.

Your tasks are:
1.  **Analyze User Request**: Carefully understand the user's description of the web application they want.
2.  **Identify Pages**: Determine all the distinct HTML pages required for the application.
3.  **Define Page Structure**: For each identified page, list the key sections.
4.  **Specify Styling Approach**: Mandate Tailwind CSS.
5.  **Enforce Relative Paths**: Stress the use of relative paths for internal links.
6.  **Define Shared Elements**: Specify common elements like a consistent header (with navigation) and footer that should appear on multiple pages.
7.  **Output Format**:
    *   First, output a `<shared_context>` block containing a JSON object with `application_description`, `global_styling`, and `shared_elements`.
    *   Then, for EACH page identified, output a separate `<task>` block containing a JSON object detailing that specific page (`file_path`, `title`, `description`, `sections`).
    *   Do NOT include any other explanatory text outside these blocks.

**Example Output Structure:**

<shared_context>
{
  "application_description": "A brief summary of the web application to be built, based on the user's request. Include key functionalities expected.",
  "global_styling": {
    "framework": "Tailwind CSS",
    "notes": [
      "Use Tailwind CSS classes for all styling aspects.",
      "Ensure the design is responsive across common screen sizes (mobile, tablet, desktop) using Tailwind's responsive prefixes.",
      "All internal links between pages of this application MUST use relative paths.",
      "Each HTML page should include the Tailwind CSS CDN link in the <head>: <script src='https://cdn.tailwindcss.com'></script>.",
      "Use semantic HTML5 elements where appropriate.",
      "Define a specific color palette with hex codes. For example: Primary: #RRGGBB, Secondary: #RRGGBB, Accent: #RRGGBB, Text: #RRGGBB, Background: #RRGGBB.",
      "Establish basic typography guidelines (e.g., font family for headings and body, base font size).",
      "Promote consistent spacing and padding throughout the application.",
      "Ensure good color contrast for accessibility."
    ]
  },
  "shared_elements": {
    "header": "A consistent header should be present on all pages, typically containing the site logo/name and main navigation links.",
    "footer": "A consistent footer should be present on all pages, typically containing copyright information and perhaps secondary links.",
    "navigation_links": ["Example: Home", "Example: About", "Example: Services", "Example: Contact"]
  }
}
</shared_context>
<task>
{
  "file_path": "index.html",
  "title": "Homepage",
  "description": "Brief description of this page's purpose and content.",
  "sections": [
    "Header (with navigation)",
    "Hero Section",
    "Key Features",
    "Footer"
  ]
}
</task>
<task>
{
  "file_path": "about.html",
  "title": "About Us",
  "description": "Information about the company.",
  "sections": [
    "Header (with navigation)",
    "Company History",
    "Team Bios",
    "Footer"
  ]
}
</task>
// ... more task blocks if more pages are identified.

**Important**: Do NOT generate any HTML code yourself. Your sole output is the shared context and the series of task blocks.
""",
)
async def frontend_analyzer():
    """Analyzes user requirements and creates a structured plan for frontend generation."""
    pass


@app.agent(
    name="page_generator_delegatee",
    description="Generates HTML code for a single web page using Tailwind CSS, based on a task JSON and shared context.",
    system_prompt="""You are an expert HTML and Tailwind CSS Code Generator for single pages.
You will receive input in two parts, often concatenated:
1.  A 'Shared Context' JSON string, typically looking like:
    ```json
    // Shared Context (from frontend_analyzer)
    {
      "application_description": "A simple two-page website about a fictional company.",
      "global_styling": {
        "framework": "Tailwind CSS",
        "notes": [
          "Use Tailwind CSS classes for all styling aspects.",
          "Ensure the design is responsive...",
          "All internal links ... MUST use relative paths.",
          "Each HTML page should include ... <script src='https://cdn.tailwindcss.com'></script>.",
          "Use semantic HTML5 elements."
        ]
      }
    }
    ```
2.  A 'Task' JSON string for a single page, typically looking like:
    ```json
    // Task (from frontend_analyzer)
    {
      "file_path": "index.html",
      "title": "Welcome to MyApp",
      "description": "The main landing page for MyApp.",
      "sections": ["Header (with navigation: Home, About)", "Hero Section: Welcome to MyApp", "Main Content: Brief intro", "Footer"]
    }
    ```

Your task is to generate the complete HTML code for the single page specified in the 'Task' JSON, adhering to the 'Shared Context'.

**Your Responsibilities:**

1.  **Parse Input**: Understand that the input might be a concatenation of shared context and the task. The task JSON is your primary focus for page details.
2.  **Generate HTML**: Create a complete, standalone HTML document for the page.
    *   Use the `file_path` from the task JSON for the `<file path="...">` wrapper.
    *   Use the `title` from the task JSON for the HTML `<title>` tag.
    *   Implement all `sections` listed for that page from the task JSON. Be creative and fill them with plausible placeholder content and structure.
3.  **HTML Structure**: The HTML file must:
    *   Start with `<!DOCTYPE html>`.
    *   Include `<html lang="en">`, `<head>`, and `<body>` tags.
    *   Inside `<head>`:
        *   `<meta charset="UTF-8">`
        *   `<meta name="viewport" content="width=device-width, initial-scale=1.0">`
        *   The correct page `<title>`.
        *   The Tailwind CSS CDN link (as specified in shared context, typically `<script src="https://cdn.tailwindcss.com"></script>`).
4.  **Tailwind CSS**:
    *   Style ALL elements using Tailwind CSS classes directly in the HTML, following guidelines in `global_styling.notes`.
    *   Implement responsive design.
    *   Create visually appealing layouts.
5.  **Relative Paths**:
    *   All links (`<a>` tags) navigating between pages of this application **MUST use relative paths** based on their `file_path` values (guided by `global_styling.notes` and the page's `file_path`).
6.  **Content**:
    *   Generate plausible placeholder content for each section.
    *   Use semantic HTML5 elements.
7.  **Output Format**:
    *   Wrap the complete HTML code for the page within `<file path="THE_ACTUAL_FILE_PATH.html">` and `</file>` tags.
    *   Replace `THE_ACTUAL_FILE_PATH.html` with the `file_path` from the input task JSON.
    *   Your entire response MUST consist of this single `<file>...</file>` block.
    *   **Do NOT include any other text, explanations, or markdown formatting (like ```html) outside of the `<file>...</file>` block.**

**Example of output:**
<file path="index.html">
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <script src="https://cdn.tailwindcss.com"></script>
    <title>Homepage</title>
</head>
<body>
    <!-- ... HTML content based on task and shared context ... -->
</body>
</html>
</file>
Ensure your output strictly adheres to this format.
""",
)
async def page_generator_delegatee():
    """Generates HTML for a single page based on a task and shared context."""
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

If no valid `<file ...>` blocks are found or files have already been written, respond with: "No files found to write."

**Do not include any other text or explanations in your response.**
""",
    tools=["write_file"],
)
async def file_writer():
    """Writes the generated code to files."""
    pass


@app.agent(
    name="task_summarizer",
    description="Summarizes the result of a single page generation task, focusing on the file created and its main sections.",
    system_prompt="""You are a Task Summarizer. Your input will be the output of a page generation process, which includes the full HTML content of a generated web page, wrapped in `<file path="...">...</file>` tags.

Your task is to produce a concise summary of what was generated. The summary should include:
1. The file path of the generated HTML page.
2. A brief mention of the main sections or key features implemented in that page based on its content.

Example Input:
```
<file path="about.html">
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <script src="https://cdn.tailwindcss.com"></script>
    <title>About Us</title>
</head>
<body>
    <header>...</header>
    <main>
        <section id="company-history">...</section>
        <section id="team-bios">...</section>
    </main>
    <footer>...</footer>
</body>
</html>
</file>
```

Example Summary Output:
"Successfully generated page 'about.html'. It includes a header, sections for company history and team bios, and a footer."

Keep the summary brief and to the point. Do not include the HTML content in your summary.
""",
)
async def task_summarizer():
    """Summarizes the output of a page generation task."""
    pass


# Create the frontend generation flow
frontend_flow = Flow(
    flow_name="frontend_generation",
    description="Generates a complete frontend implementation based on user requirements.",
)

frontend_flow2 = Flow(
    flow_name="frontend_generation_CoA",
    description="Generates a complete frontend implementation based on user requirements, using Chain of Agents",
)

sequential_pattern = SequentialPattern(
    pattern_name="frontend_generation_sequence",
    steps=["frontend_generator", "file_writer"],
)

frontend_flow.add_step(
    DelegatePattern(
        pattern_name="page_creation_delegation",
        delegator_agent="frontend_analyzer",
        delegatee_agent=sequential_pattern,
        processing_mode=ProcessingMode.SEQUENTIAL,
        task_extraction_regex=r"<task>(.*?)</task>",
        shared_memory_extraction_regex=r"<shared_context>(.*?)</shared_context>",
    )
)

frontend_flow2.add_step(
    DelegatePattern(
        pattern_name="page_creation_delegation",
        delegator_agent="frontend_analyzer",
        delegatee_agent=sequential_pattern,
        processing_mode=ProcessingMode.SEQUENTIAL,
        task_extraction_regex=r"<task>(.*?)</task>",
        shared_memory_extraction_regex=r"<shared_context>(.*?)</shared_context>",
        chain_of_agents=True,
        summary_agent="task_summarizer",
    )
)


# Register the flow with the app
app.register_flow(frontend_flow)
app.register_flow(frontend_flow2)


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
