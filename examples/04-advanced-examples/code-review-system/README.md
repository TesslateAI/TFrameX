# AI-Powered Code Review System

An advanced TFrameX example demonstrating sophisticated multi-agent code analysis, security scanning, and automated code review processes.

## 🎯 What This Example Demonstrates

- **Multi-agent collaboration** for comprehensive code analysis
- **Specialized agents** for different aspects of code review
- **Parallel processing** for efficient analysis
- **Report generation** and documentation
- **Integration patterns** for real-world applications

## 🏗️ Architecture

```
Code Review Flow:
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  Code Scanner   │    │ Security Analyzer│    │Performance Audit│
│ (Structure &    │◄──►│ (Vulnerabilities)│◄──►│ (Bottlenecks)   │
│  Syntax)        │    │                  │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────┬───────────────────────────────┘
                         ▼
                ┌─────────────────┐
                │ Review Coordinator│
                │ (Final Report)   │
                └─────────────────┘
```

## 🚀 Features

### **Specialized Agents**
- **CodeAnalyzer**: Static analysis, syntax, structure
- **SecurityScanner**: Vulnerability detection, dependency analysis
- **PerformanceAuditor**: Performance bottlenecks, optimization opportunities
- **QualityAssessor**: Code quality metrics, best practices
- **ReviewCoordinator**: Orchestrates analysis and generates final reports

### **Analysis Capabilities**
- Syntax and structure validation
- Security vulnerability detection
- Performance bottleneck identification
- Code quality assessment
- Dependency analysis
- Documentation coverage
- Test coverage analysis

### **Reporting Features**
- Comprehensive review reports
- Severity-based issue classification
- Actionable recommendations
- Integration with CI/CD workflows

## 📁 Project Structure

```
code-review-system/
├── README.md              # This guide
├── requirements.txt       # Dependencies
├── .env.example          # Environment template
├── main.py               # Main application
├── config/
│   ├── agents.py         # Agent definitions
│   ├── tools.py          # Tool definitions
│   └── flows.py          # Flow configurations
├── data/
│   ├── test_files/       # Sample code files for testing
│   └── reports/          # Generated review reports
└── docs/
    ├── setup.md          # Setup instructions
    ├── usage.md          # Usage examples
    └── integration.md    # CI/CD integration guide
```

## 🔧 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment
```bash
cp .env.example .env
# Edit .env with your LLM settings
```

### 3. Run the Example
```bash
# Interactive mode
python main.py

# Analyze specific file
python main.py --file path/to/code.py

# Analyze directory
python main.py --directory path/to/project

# Generate report only
python main.py --file code.py --report-only
```

## 💻 Usage Examples

### **Interactive Mode**
```python
# Start interactive review session
async with app.run_context() as rt:
    await rt.interactive_chat(default_agent_name="ReviewCoordinator")
```

### **Programmatic Analysis**
```python
# Analyze a specific file
review_result = await analyze_code_file("example.py")
print(review_result.security_issues)
print(review_result.performance_recommendations)
```

### **Batch Processing**
```python
# Analyze multiple files
files = ["file1.py", "file2.js", "file3.java"]
results = await batch_analyze_files(files)
generate_summary_report(results)
```

## 🔍 Analysis Types

### **Security Analysis**
- SQL injection vulnerabilities
- XSS attack vectors
- Insecure dependencies
- Hardcoded secrets
- Unsafe deserialization
- Authentication bypasses

### **Performance Analysis**
- Algorithm complexity issues
- Memory leaks
- Inefficient database queries
- Resource bottlenecks
- Caching opportunities

### **Quality Analysis**
- Code complexity metrics
- Naming conventions
- Documentation coverage
- Error handling patterns
- Design pattern adherence

### **Structure Analysis**
- Module organization
- Dependency management
- Architecture compliance
- Code duplication
- Dead code detection

## 🎮 Interactive Features

### **Review Dashboard**
```bash
# Start the interactive dashboard
python main.py --dashboard
```

### **Custom Analysis**
```bash
# Focus on specific analysis types
python main.py --focus security,performance
python main.py --exclude quality
```

### **Integration Mode**
```bash
# CI/CD integration
python main.py --ci-mode --output-format json
```

## 📊 Report Examples

### **Security Report**
```
🔒 SECURITY ANALYSIS REPORT
==========================
Critical Issues: 2
High Issues: 5
Medium Issues: 12

Critical Issues:
- Line 45: SQL injection vulnerability in user_login()
- Line 128: Hardcoded API key in configuration

Recommendations:
1. Use parameterized queries for database operations
2. Move secrets to environment variables
3. Implement input sanitization
```

### **Performance Report**
```
⚡ PERFORMANCE ANALYSIS REPORT
=============================
Bottlenecks Found: 8
Optimization Opportunities: 15

Major Issues:
- Line 67: O(n²) algorithm in data processing loop
- Line 203: Blocking I/O operation in async context
- Line 341: Memory leak in resource management

Recommendations:
1. Optimize sorting algorithm to O(n log n)
2. Use async/await for I/O operations
3. Implement proper resource cleanup
```

## 🔧 Configuration

### **Environment Variables**
```env
# LLM Configuration
OPENAI_API_KEY=your_api_key
OPENAI_API_BASE=https://api.openai.com/v1
OPENAI_MODEL_NAME=gpt-4

# Analysis Settings
SECURITY_SCAN_DEPTH=deep
PERFORMANCE_THRESHOLD=medium
QUALITY_STANDARDS=strict

# Reporting
REPORT_FORMAT=markdown
OUTPUT_DIRECTORY=./reports
INCLUDE_SUGGESTIONS=true
```

### **Custom Rules**
```python
# config/rules.py
SECURITY_RULES = [
    "no_hardcoded_secrets",
    "validate_inputs", 
    "secure_dependencies"
]

PERFORMANCE_RULES = [
    "optimize_loops",
    "async_best_practices",
    "memory_management"
]
```

## 🚀 Advanced Usage

### **Custom Agents**
```python
@app.agent(
    name="CustomSecurityAgent",
    tools=["custom_vulnerability_scanner"],
    system_prompt="Specialized security analysis for financial applications..."
)
async def custom_security_agent():
    pass
```

### **Pipeline Integration**
```yaml
# GitHub Actions example
- name: Code Review
  run: |
    python code-review-system/main.py \
      --directory . \
      --output-format json \
      --fail-on critical
```

### **Custom Reports**
```python
# Generate custom report formats
await generate_report(
    analysis_results,
    format="html",
    template="security_focused",
    include_graphs=True
)
```

## 🔌 Integration Examples

### **VS Code Extension**
```json
{
  "command": "tframex.codeReview",
  "args": ["--file", "${file}", "--format", "json"]
}
```

### **Pre-commit Hook**
```bash
#!/bin/sh
python code-review-system/main.py \
  --directory . \
  --quick-scan \
  --fail-on high
```

### **CI/CD Pipeline**
```yaml
code_review:
  script:
    - python code-review-system/main.py --ci-mode
  artifacts:
    reports:
      - reports/code_review.json
```

## 🧪 Testing

```bash
# Run example with test files
python main.py --directory data/test_files

# Test specific analysis types
python main.py --test security
python main.py --test performance
python main.py --test quality
```

## 🤝 Extending the System

### **Adding New Analysis Types**
1. Create new agent in `config/agents.py`
2. Define analysis tools in `config/tools.py`
3. Update coordination flow in `config/flows.py`
4. Add report templates

### **Custom Integrations**
1. Implement custom tools for your tech stack
2. Create specialized agents for domain-specific analysis
3. Add custom report formats
4. Integrate with existing development tools

## 📚 Next Steps

After exploring this example:

1. **Customize** the agents for your specific codebase
2. **Integrate** with your CI/CD pipeline
3. **Extend** with additional analysis types
4. **Build** custom reporting dashboards

## 🐛 Troubleshooting

### Common Issues

**Large codebase analysis is slow**
- Use `--quick-scan` for faster analysis
- Focus on specific directories with `--include-dirs`
- Enable parallel processing with `--parallel`

**High memory usage**
- Process files in batches with `--batch-size`
- Exclude large binary files with `--exclude-patterns`

**False positives in security scan**
- Adjust sensitivity with `--security-threshold`
- Add custom ignore rules in `config/ignore_rules.yaml`

## 📄 License

This example is provided under the MIT License.