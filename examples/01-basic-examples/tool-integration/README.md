# Tool Integration - TFrameX Advanced Basic Example

An advanced example demonstrating comprehensive tool integration with external APIs, databases, web scraping, and file processing capabilities.

## 🎯 What You'll Learn

- **External API Integration**: Weather, news, and notification services
- **Database Operations**: SQLite database management and querying
- **Web Scraping**: Content extraction from web pages
- **File Processing**: CSV analysis and report generation
- **Workflow Coordination**: Multi-tool orchestration for complex tasks

## 📁 Project Structure

```
tool-integration/
├── README.md              # This guide
├── requirements.txt       # Dependencies
├── .env.example          # Environment template
├── main.py               # Main application
├── config/
│   ├── agents.py         # Agent definitions
│   └── tools.py          # Tool definitions
├── data/
│   ├── example.db        # SQLite database (created automatically)
│   ├── downloads/        # Downloaded files
│   └── reports/          # Generated reports
└── docs/
    ├── setup.md          # Setup instructions
    └── api_integrations.md # API integration guide
```

## 🚀 Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your settings

# Run the example
python main.py
```

## 🔧 Tool Categories

### **🌐 External API Tools**
- **Weather API**: Get current weather for any city
- **News API**: Fetch latest headlines by topic
- **Email Service**: Send notifications (simulated in demo)

### **🗄️ Database Tools**
- **Table Creation**: Create SQLite tables with custom schemas
- **Data Insertion**: Insert JSON data into tables
- **Data Querying**: Query with conditions and get formatted results

### **🌍 Web Scraping Tools**
- **Content Extraction**: Scrape text content from web pages
- **File Downloads**: Download and save files from URLs
- **Content Processing**: Clean and analyze scraped data

### **📄 File Processing Tools**
- **CSV Analysis**: Process CSV files and extract statistics
- **Report Generation**: Create reports in multiple formats (TXT, MD, HTML)

## 💻 Agent Specializations

### **APIAgent**
```python
# Handles external API integrations
await api_agent.run("What's the weather in London and any recent news about climate?")
```

### **DatabaseAgent**
```python
# Manages data storage and retrieval
await db_agent.run("Create a users table and add some sample customer data")
```

### **WebAgent**
```python
# Scrapes and processes web content
await web_agent.run("Scrape the latest Python news from python.org")
```

### **IntegrationCoordinator**
```python
# Orchestrates complex multi-tool workflows
await coordinator.run("Research Paris weather, save to database, and generate a travel report")
```

## 🎮 Demo Modes

### **1. API Integration Demo**
```bash
python main.py
# Select option 1
```
- Weather information retrieval
- News headline fetching
- Email notification sending

### **2. Database Operations Demo**
```bash
python main.py
# Select option 2
```
- Table creation and schema design
- Data insertion with JSON formatting
- Complex queries and result formatting

### **3. Web Scraping Demo**
```bash
python main.py
# Select option 3
```
- Content extraction from web pages
- File downloading and storage
- Content analysis and summarization

### **4. Integration Coordinator Demo**
```bash
python main.py
# Select option 4
```
- Multi-step workflow execution
- Cross-tool data coordination
- Comprehensive result synthesis

## 🔧 Configuration

### **Demo Mode vs Production**

**Demo Mode** (default):
- Uses mock data for APIs
- Simulates external services
- Safe for testing without API keys

**Production Mode**:
- Requires real API keys
- Connects to actual external services
- Set `DEMO_MODE=false` in .env

### **API Integration Setup**

For production use, add these API keys to your .env:

```env
# Weather API
OPENWEATHER_API_KEY=your_key_here

# News API  
NEWS_API_KEY=your_key_here

# Email Service
EMAIL_API_KEY=your_key_here
EMAIL_FROM=your_email@domain.com
```

### **Database Configuration**

```env
# SQLite database location
DATABASE_PATH=./data/example.db

# Or use PostgreSQL/MySQL in production
# DATABASE_URL=postgresql://user:pass@localhost/dbname
```

## 📊 Example Workflows

### **Market Research Workflow**
```python
# 1. Get weather data for target cities
# 2. Fetch news about market trends
# 3. Store data in database
# 4. Generate comprehensive report
# 5. Email report to stakeholders

coordinator_request = """
I need a market research report for expanding our business to London and Paris.
Please:
1. Get current weather for both cities
2. Find recent business news about these markets
3. Store this data in our database
4. Generate a comprehensive report
5. Email the report to research@company.com
"""
```

### **Content Analysis Workflow**
```python
# 1. Scrape content from competitor websites
# 2. Process and analyze the content
# 3. Store insights in database
# 4. Generate competitive analysis report

web_analysis_request = """
Analyze our competitor's website content:
1. Scrape their latest blog posts
2. Extract key topics and themes
3. Store the analysis in our content database
4. Generate a competitive content report
"""
```

### **Data Pipeline Workflow**
```python
# 1. Download CSV data files
# 2. Process and clean the data
# 3. Store processed data in database
# 4. Generate statistical analysis report

data_pipeline_request = """
Set up a data processing pipeline:
1. Download the sales data CSV from our server
2. Process and analyze the sales statistics
3. Store the processed data in our analytics database
4. Generate monthly sales performance report
"""
```

## 🔍 Tool Integration Patterns

### **Sequential Tool Chains**
```python
# Tools executed in sequence, output passed to next tool
weather_data = await get_weather("London")
news_data = await get_news("London business")
report = await generate_report("London Analysis", f"{weather_data}\n{news_data}")
```

### **Parallel Tool Execution**
```python
# Multiple tools executed simultaneously
async with asyncio.TaskGroup() as tg:
    weather_task = tg.create_task(get_weather("Paris"))
    news_task = tg.create_task(get_news("Paris"))
    
results = await asyncio.gather(weather_task, news_task)
```

### **Conditional Tool Selection**
```python
# Tool selection based on data or conditions
if "emergency" in user_request:
    await send_email("urgent@company.com", "Emergency Alert", details)
else:
    await generate_report("Standard Report", details)
```

## 🛠️ Extending with Custom Tools

### **Adding New API Integration**
```python
@app.tool(description="Custom API integration")
async def custom_api_call(endpoint: str, params: dict) -> str:
    # Custom API integration logic
    pass
```

### **Adding Database Support**
```python
@app.tool(description="Advanced database operations")
async def advanced_query(sql: str, params: list) -> str:
    # Complex database operations
    pass
```

### **Adding File Format Support**
```python
@app.tool(description="Process Excel files")
async def process_excel(filename: str) -> str:
    # Excel file processing logic
    pass
```

## 🚨 Error Handling & Resilience

### **Built-in Error Handling**
- API timeout and retry logic
- Database connection error recovery
- File operation error management
- Graceful degradation for failed services

### **Monitoring & Logging**
- Comprehensive operation logging
- Error tracking and reporting
- Performance monitoring
- Tool usage statistics

## 📚 Production Considerations

### **Security**
- API key management and rotation
- Input validation and sanitization
- Rate limiting for external APIs
- Secure database connections

### **Performance**
- Connection pooling for databases
- Async operations for all I/O
- Caching for frequently accessed data
- Batch operations for efficiency

### **Reliability**
- Circuit breaker pattern for external services
- Retry logic with exponential backoff
- Health checks for all integrations
- Fallback mechanisms for critical operations

## 🔍 What's Next?

After mastering tool integration:

1. **Explore Pattern Examples**: [Sequential Pattern](../../02-pattern-examples/sequential-pattern/)
2. **Try Advanced Examples**: [Code Review System](../../04-advanced-examples/code-review-system/)
3. **Build Custom Integrations**: Add your own APIs and services
4. **Scale to Production**: Implement monitoring and error handling

## 🐛 Troubleshooting

### **Common Issues**

**API calls failing**
- Check API keys in .env file
- Verify network connectivity
- Enable demo mode for testing

**Database errors**
- Ensure data directory exists
- Check file permissions
- Verify SQLite installation

**File processing issues**
- Check file permissions
- Verify file format compatibility
- Ensure sufficient disk space

## 📄 License

This example is provided under the MIT License.