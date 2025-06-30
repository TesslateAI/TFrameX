"""
Tool definitions for Simple Agent example.

This module demonstrates various types of tools including:
- Mathematical operations
- File operations
- Data processing
- Utility functions
"""

import json
import os
import math
from datetime import datetime
from typing import List, Dict, Any

from tframex import TFrameXApp


def setup_tools(app: TFrameXApp):
    """Configure all tools for the Simple Agent example."""
    
    # === Mathematical Tools ===
    
    @app.tool(description="Performs mathematical calculations safely")
    async def calculate(expression: str) -> str:
        """
        Safely evaluate mathematical expressions.
        
        Args:
            expression: Mathematical expression (e.g., "2 + 3 * 4")
            
        Returns:
            Calculation result or error message
        """
        try:
            # Safe evaluation - only allow basic math operations
            allowed_names = {
                k: v for k, v in math.__dict__.items() 
                if not k.startswith("__")
            }
            allowed_names.update({
                "abs": abs, "round": round, "min": min, "max": max,
                "sum": sum, "pow": pow
            })
            
            result = eval(expression, {"__builtins__": {}}, allowed_names)
            return f"Calculation result: {result}"
            
        except Exception as e:
            return f"Calculation error: {str(e)}"
    
    
    @app.tool(description="Saves a calculation result to memory")
    async def save_result(result: str, label: str = "calculation") -> str:
        """
        Save a calculation result for later reference.
        
        Args:
            result: The result to save
            label: Label for the saved result
            
        Returns:
            Confirmation message
        """
        try:
            # Create data directory if it doesn't exist
            os.makedirs("data", exist_ok=True)
            
            # Load existing results
            results_file = "data/saved_results.json"
            if os.path.exists(results_file):
                with open(results_file, "r") as f:
                    saved_results = json.load(f)
            else:
                saved_results = {}
            
            # Save new result with timestamp
            saved_results[label] = {
                "result": result,
                "timestamp": datetime.now().isoformat()
            }
            
            # Write back to file
            with open(results_file, "w") as f:
                json.dump(saved_results, f, indent=2)
            
            return f"Result saved as '{label}': {result}"
            
        except Exception as e:
            return f"Error saving result: {str(e)}"
    
    
    @app.tool(description="Retrieves a previously saved calculation result")
    async def get_saved_result(label: str) -> str:
        """
        Retrieve a previously saved calculation result.
        
        Args:
            label: Label of the saved result
            
        Returns:
            The saved result or error message
        """
        try:
            results_file = "data/saved_results.json"
            if not os.path.exists(results_file):
                return "No saved results found"
            
            with open(results_file, "r") as f:
                saved_results = json.load(f)
            
            if label in saved_results:
                result_data = saved_results[label]
                return f"Saved result '{label}': {result_data['result']} (saved: {result_data['timestamp']})"
            else:
                available = list(saved_results.keys())
                return f"Result '{label}' not found. Available: {available}"
                
        except Exception as e:
            return f"Error retrieving result: {str(e)}"
    
    
    # === File Operations ===
    
    @app.tool(description="Creates a text file with specified content")
    async def create_file(filename: str, content: str) -> str:
        """
        Create a text file with the given content.
        
        Args:
            filename: Name of the file to create
            content: Content to write to the file
            
        Returns:
            Success or error message
        """
        try:
            with open(filename, "w") as f:
                f.write(content)
            return f"File '{filename}' created successfully"
        except Exception as e:
            return f"Error creating file: {str(e)}"
    
    
    @app.tool(description="Reads content from a text file")
    async def read_file(filename: str) -> str:
        """
        Read content from a text file.
        
        Args:
            filename: Name of the file to read
            
        Returns:
            File content or error message
        """
        try:
            with open(filename, "r") as f:
                content = f.read()
            return f"Content of '{filename}':\n{content}"
        except FileNotFoundError:
            return f"File '{filename}' not found"
        except Exception as e:
            return f"Error reading file: {str(e)}"
    
    
    @app.tool(description="Lists files in the current directory")
    async def list_files() -> str:
        """
        List all files in the current directory.
        
        Returns:
            List of files and directories
        """
        try:
            files = os.listdir(".")
            files.sort()
            
            file_list = []
            for file in files:
                if os.path.isdir(file):
                    file_list.append(f"📁 {file}/")
                else:
                    size = os.path.getsize(file)
                    file_list.append(f"📄 {file} ({size} bytes)")
            
            return "Files in current directory:\n" + "\n".join(file_list)
            
        except Exception as e:
            return f"Error listing files: {str(e)}"
    
    
    @app.tool(description="Deletes a file")
    async def delete_file(filename: str) -> str:
        """
        Delete a file.
        
        Args:
            filename: Name of the file to delete
            
        Returns:
            Success or error message
        """
        try:
            if os.path.exists(filename):
                os.remove(filename)
                return f"File '{filename}' deleted successfully"
            else:
                return f"File '{filename}' not found"
        except Exception as e:
            return f"Error deleting file: {str(e)}"
    
    
    # === Data Processing Tools ===
    
    @app.tool(description="Processes and analyzes JSON data")
    async def analyze_data(data_str: str) -> str:
        """
        Analyze JSON data and provide insights.
        
        Args:
            data_str: JSON string to analyze
            
        Returns:
            Analysis results
        """
        try:
            data = json.loads(data_str)
            
            analysis = []
            analysis.append(f"Data type: {type(data).__name__}")
            
            if isinstance(data, dict):
                analysis.append(f"Keys: {list(data.keys())}")
                analysis.append(f"Number of keys: {len(data)}")
                
                # Analyze values
                numeric_values = []
                for key, value in data.items():
                    if isinstance(value, (int, float)):
                        numeric_values.append(value)
                
                if numeric_values:
                    analysis.append(f"Numeric values found: {len(numeric_values)}")
                    analysis.append(f"Sum: {sum(numeric_values)}")
                    analysis.append(f"Average: {sum(numeric_values) / len(numeric_values):.2f}")
                    analysis.append(f"Min: {min(numeric_values)}")
                    analysis.append(f"Max: {max(numeric_values)}")
            
            elif isinstance(data, list):
                analysis.append(f"List length: {len(data)}")
                if data:
                    analysis.append(f"First item type: {type(data[0]).__name__}")
            
            return "Data Analysis:\n" + "\n".join(analysis)
            
        except json.JSONDecodeError:
            return "Error: Invalid JSON data"
        except Exception as e:
            return f"Error analyzing data: {str(e)}"
    
    
    @app.tool(description="Gets current date and time information")
    async def get_datetime_info() -> str:
        """
        Get current date and time information.
        
        Returns:
            Formatted date and time information
        """
        now = datetime.now()
        
        info = [
            f"Current date: {now.strftime('%Y-%m-%d')}",
            f"Current time: {now.strftime('%H:%M:%S')}",
            f"Day of week: {now.strftime('%A')}",
            f"Month: {now.strftime('%B')}",
            f"Year: {now.year}",
            f"ISO format: {now.isoformat()}"
        ]
        
        return "Date/Time Information:\n" + "\n".join(info)
    
    
    # === Utility Tools ===
    
    @app.tool(description="Converts between different units")
    async def convert_units(value: float, from_unit: str, to_unit: str) -> str:
        """
        Convert between different units.
        
        Args:
            value: Value to convert
            from_unit: Source unit
            to_unit: Target unit
            
        Returns:
            Conversion result
        """
        # Temperature conversions
        if from_unit.lower() == "celsius" and to_unit.lower() == "fahrenheit":
            result = (value * 9/5) + 32
            return f"{value}°C = {result:.2f}°F"
        elif from_unit.lower() == "fahrenheit" and to_unit.lower() == "celsius":
            result = (value - 32) * 5/9
            return f"{value}°F = {result:.2f}°C"
        
        # Length conversions (basic)
        length_to_meters = {
            "mm": 0.001, "cm": 0.01, "m": 1, "km": 1000,
            "inch": 0.0254, "ft": 0.3048, "yard": 0.9144, "mile": 1609.34
        }
        
        if from_unit.lower() in length_to_meters and to_unit.lower() in length_to_meters:
            meters = value * length_to_meters[from_unit.lower()]
            result = meters / length_to_meters[to_unit.lower()]
            return f"{value} {from_unit} = {result:.4f} {to_unit}"
        
        return f"Conversion from {from_unit} to {to_unit} not supported"