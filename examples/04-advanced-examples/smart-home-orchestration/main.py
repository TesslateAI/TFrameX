#!/usr/bin/env python3
"""
TFrameX Smart Home Orchestration - Advanced Example

Demonstrates intelligent home automation using TFrameX's multi-agent architecture.
Multiple specialized agents work together to manage different aspects of a smart home,
making intelligent decisions based on occupancy, preferences, energy efficiency,
and security considerations.

System Features:
- Multi-agent coordination for different home systems
- Context-aware automation based on occupancy and time
- Energy optimization and cost management
- Security monitoring and response
- Preference learning and adaptation
- Emergency response coordination
"""

import asyncio
import json
import logging
from datetime import datetime, time
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from dotenv import load_dotenv
from tframex import TFrameX, Message, Flow
from tframex.llms import OpenAILLM
from tframex.memory import InMemoryMemoryStore

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize TFrameX app
app = TFrameX(
    default_llm=OpenAILLM(),
    default_memory_store_factory=InMemoryMemoryStore
)

# ===== SMART HOME DATA MODELS =====

class RoomType(Enum):
    LIVING_ROOM = "living_room"
    KITCHEN = "kitchen"
    BEDROOM = "bedroom"
    BATHROOM = "bathroom"
    OFFICE = "office"
    GARAGE = "garage"

class DeviceType(Enum):
    LIGHTS = "lights"
    THERMOSTAT = "thermostat"
    SECURITY_CAMERA = "security_camera"
    DOOR_LOCK = "door_lock"
    APPLIANCE = "appliance"
    SENSOR = "sensor"

@dataclass
class HomeState:
    """Current state of the smart home."""
    occupied_rooms: List[str]
    current_temperature: float
    target_temperature: float
    security_status: str
    energy_usage: float
    time_of_day: str
    weather_outside: str
    resident_preferences: Dict[str, str]

@dataclass
class DeviceState:
    """State of a smart home device."""
    device_id: str
    device_type: DeviceType
    room: str
    status: str
    settings: Dict[str, str]
    energy_usage: float

# ===== SPECIALIZED AGENTS =====

@app.agent(
    name="HomeOrchestrator",
    description="Main coordinator that orchestrates all smart home agents and makes high-level decisions",
    system_prompt="""
    You are the central home orchestration system responsible for:
    
    1. **System Coordination**: Coordinate between all smart home subsystems
    2. **Decision Making**: Make high-level decisions about home automation
    3. **Priority Management**: Balance competing needs (comfort, security, efficiency)
    4. **Conflict Resolution**: Resolve conflicts between different agent recommendations
    5. **Emergency Coordination**: Coordinate emergency responses across all systems
    
    ORCHESTRATION PRINCIPLES:
    - Safety and security always take priority
    - Energy efficiency is important but not at the expense of comfort
    - Learn and adapt to resident preferences over time
    - Minimize disruption to daily routines
    - Coordinate smooth transitions between different home states
    
    When making decisions, consider input from all specialist agents and provide
    clear, coordinated instructions for optimal home management.
    """
)
async def home_orchestrator():
    """Central coordinator for all smart home systems."""
    pass

@app.agent(
    name="LightingAgent",
    description="Manages all lighting systems throughout the home",
    system_prompt="""
    You are the intelligent lighting management system responsible for:
    
    1. **Occupancy-Based Control**: Adjust lighting based on room occupancy
    2. **Circadian Rhythm**: Support natural sleep/wake cycles with appropriate lighting
    3. **Energy Efficiency**: Optimize lighting for energy savings
    4. **Ambiance Control**: Create appropriate lighting for different activities
    5. **Security Lighting**: Coordinate with security for deterrent lighting
    
    LIGHTING STRATEGIES:
    - Bright, cool light during morning and work hours
    - Warm, dim light in evening for relaxation
    - Motion-activated lighting in corridors and bathrooms
    - Automated outdoor lighting based on sunset/sunrise
    - Energy-efficient scheduling and dimming
    
    Consider time of day, occupancy, activity type, and energy efficiency.
    Provide specific lighting recommendations with brightness levels and color temperatures.
    """
)
async def lighting_agent():
    """Manages intelligent lighting throughout the home."""
    pass

@app.agent(
    name="ClimateAgent", 
    description="Controls heating, cooling, and ventilation systems",
    system_prompt="""
    You are the climate control system responsible for:
    
    1. **Temperature Management**: Maintain optimal temperature in occupied areas
    2. **Energy Optimization**: Balance comfort with energy efficiency
    3. **Zone Control**: Manage different temperatures in different zones
    4. **Schedule Adaptation**: Learn and adapt to resident schedule patterns
    5. **Weather Integration**: Adjust for external weather conditions
    
    CLIMATE STRATEGIES:
    - Pre-cool/pre-heat before residents arrive home
    - Reduce heating/cooling in unoccupied areas
    - Use natural ventilation when weather permits
    - Optimize for time-of-use electricity rates
    - Maintain healthy humidity levels
    
    Consider occupancy patterns, weather, energy costs, and comfort preferences.
    Provide specific temperature and ventilation recommendations.
    """
)
async def climate_agent():
    """Manages home climate control systems."""
    pass

@app.agent(
    name="SecurityAgent",
    description="Monitors and manages home security systems",
    system_prompt="""
    You are the home security system responsible for:
    
    1. **Intrusion Detection**: Monitor for unauthorized access or unusual activity
    2. **Access Control**: Manage door locks and entry permissions
    3. **Surveillance**: Coordinate security cameras and monitoring
    4. **Emergency Response**: Detect and respond to security emergencies
    5. **Integration**: Work with other systems for comprehensive security
    
    SECURITY PRIORITIES:
    - Immediate response to potential threats
    - Minimize false alarms while maintaining vigilance
    - Coordinate with lighting for security deterrence
    - Maintain detailed logs of all security events
    - Balance security with resident convenience
    
    Always prioritize safety and security. Provide clear threat assessments
    and specific security recommendations.
    """
)
async def security_agent():
    """Manages home security and monitoring systems."""
    pass

@app.agent(
    name="EnergyAgent",
    description="Optimizes energy usage and manages utility costs",
    system_prompt="""
    You are the energy management system responsible for:
    
    1. **Usage Optimization**: Minimize energy consumption while maintaining comfort
    2. **Cost Management**: Optimize for time-of-use electricity rates
    3. **Load Balancing**: Distribute energy usage across peak and off-peak times
    4. **Renewable Integration**: Maximize use of solar/renewable energy when available
    5. **Efficiency Monitoring**: Track and improve overall home energy efficiency
    
    ENERGY STRATEGIES:
    - Shift non-critical loads to off-peak hours
    - Optimize appliance scheduling for efficiency
    - Coordinate with climate control for energy savings
    - Monitor and report on energy usage patterns
    - Suggest energy-saving opportunities
    
    Balance energy efficiency with comfort and convenience.
    Provide specific recommendations for energy optimization.
    """
)
async def energy_agent():
    """Manages energy optimization and cost efficiency."""
    pass

@app.agent(
    name="ApplianceAgent",
    description="Coordinates smart appliances and their optimal operation",
    system_prompt="""
    You are the appliance coordination system responsible for:
    
    1. **Smart Scheduling**: Optimize appliance operation timing
    2. **Maintenance Monitoring**: Track appliance health and maintenance needs
    3. **Usage Optimization**: Ensure efficient appliance operation
    4. **Load Coordination**: Coordinate with energy management for optimal timing
    5. **Convenience Enhancement**: Automate routine appliance tasks
    
    APPLIANCE STRATEGIES:
    - Schedule dishwasher and laundry during off-peak hours
    - Pre-start coffee maker and other morning appliances
    - Monitor for maintenance alerts and efficiency issues
    - Coordinate appliance usage to avoid energy spikes
    - Learn usage patterns for predictive operation
    
    Focus on convenience, efficiency, and proactive maintenance.
    Provide specific appliance scheduling and operation recommendations.
    """
)
async def appliance_agent():
    """Coordinates smart appliances throughout the home."""
    pass

@app.agent(
    name="ContextAgent",
    description="Analyzes home context, occupancy patterns, and resident preferences",
    system_prompt="""
    You are the context analysis system responsible for:
    
    1. **Occupancy Detection**: Determine who is home and where they are
    2. **Activity Recognition**: Understand what activities are taking place
    3. **Pattern Learning**: Learn and predict resident behavior patterns
    4. **Preference Analysis**: Track and adapt to changing preferences
    5. **Situation Assessment**: Provide context for other agents' decisions
    
    CONTEXT ANALYSIS:
    - Track movement patterns throughout the home
    - Recognize routine activities and schedules
    - Identify changes in behavior or preferences
    - Detect special situations (guests, parties, vacations)
    - Provide predictive insights for other systems
    
    Analyze all available data to provide rich context for home automation decisions.
    Help other agents understand the current situation and resident needs.
    """
)
async def context_agent():
    """Analyzes home context and occupancy patterns."""
    pass

# ===== ORCHESTRATION FLOWS =====

# Morning routine flow
morning_routine = Flow(
    flow_name="MorningRoutine",
    description="Coordinate morning home automation sequence"
)
morning_routine.add_step("ContextAgent")      # Assess morning context
morning_routine.add_step("ClimateAgent")      # Adjust temperature
morning_routine.add_step("LightingAgent")     # Morning lighting
morning_routine.add_step("ApplianceAgent")    # Start morning appliances
morning_routine.add_step("HomeOrchestrator")  # Final coordination

# Evening routine flow  
evening_routine = Flow(
    flow_name="EveningRoutine", 
    description="Coordinate evening home automation sequence"
)
evening_routine.add_step("ContextAgent")      # Assess evening context
evening_routine.add_step("SecurityAgent")     # Evening security check
evening_routine.add_step("LightingAgent")     # Evening lighting
evening_routine.add_step("ClimateAgent")      # Night temperature
evening_routine.add_step("HomeOrchestrator")  # Final coordination

# Energy optimization flow
energy_optimization = Flow(
    flow_name="EnergyOptimization",
    description="Optimize home energy usage while maintaining comfort"
)
energy_optimization.add_step("EnergyAgent")      # Analyze energy usage
energy_optimization.add_step("ClimateAgent")     # Climate efficiency
energy_optimization.add_step("ApplianceAgent")   # Appliance scheduling
energy_optimization.add_step("LightingAgent")    # Lighting efficiency
energy_optimization.add_step("HomeOrchestrator") # Coordinate optimization

# Security check flow
security_check = Flow(
    flow_name="SecurityCheck",
    description="Comprehensive security assessment and response"
)
security_check.add_step("SecurityAgent")      # Security assessment
security_check.add_step("ContextAgent")       # Context analysis
security_check.add_step("LightingAgent")      # Security lighting
security_check.add_step("HomeOrchestrator")   # Response coordination

# Register flows
app.register_flow(morning_routine)
app.register_flow(evening_routine)
app.register_flow(energy_optimization)
app.register_flow(security_check)

# ===== SIMULATION FUNCTIONS =====

def generate_sample_home_state() -> HomeState:
    """Generate a sample home state for demonstration."""
    return HomeState(
        occupied_rooms=["living_room", "kitchen"],
        current_temperature=72.0,
        target_temperature=73.0,
        security_status="armed_home",
        energy_usage=4.2,  # kW
        time_of_day="evening",
        weather_outside="clear, 68°F",
        resident_preferences={
            "morning_temp": "71°F",
            "evening_lighting": "warm_dim",
            "security_mode": "standard"
        }
    )

async def execute_home_automation_scenario(scenario: str, home_state: HomeState) -> Dict:
    """Execute a specific home automation scenario."""
    
    print(f"🏠 Executing Scenario: {scenario}")
    print(f"📊 Home State: {home_state.occupied_rooms}, {home_state.current_temperature}°F, {home_state.time_of_day}")
    print("=" * 60)
    
    scenario_results = {}
    
    async with app.run_context() as rt:
        # Context analysis first
        context_input = Message(role="user", content=f"""
        Analyze the current home context:
        - Occupied rooms: {home_state.occupied_rooms}
        - Current temp: {home_state.current_temperature}°F
        - Time: {home_state.time_of_day}
        - Weather: {home_state.weather_outside}
        - Scenario: {scenario}
        
        Provide context analysis for home automation decisions.
        """)
        
        context_result = await rt.call_agent("ContextAgent", context_input)
        scenario_results["context_analysis"] = context_result.current_message.content
        print(f"🧠 Context: {context_result.current_message.content[:100]}...")
        
        # Get recommendations from specialist agents
        agents_to_consult = ["LightingAgent", "ClimateAgent", "SecurityAgent", "EnergyAgent", "ApplianceAgent"]
        
        for agent_name in agents_to_consult:
            agent_input = Message(role="user", content=f"""
            Based on this scenario: {scenario}
            
            Current home state:
            - Rooms occupied: {home_state.occupied_rooms}
            - Temperature: {home_state.current_temperature}°F (target: {home_state.target_temperature}°F)
            - Time: {home_state.time_of_day}
            - Weather: {home_state.weather_outside}
            - Security: {home_state.security_status}
            - Energy usage: {home_state.energy_usage} kW
            
            Context analysis: {scenario_results["context_analysis"]}
            
            Provide your specific recommendations for this scenario.
            """)
            
            agent_result = await rt.call_agent(agent_name, agent_input)
            agent_key = agent_name.lower().replace("agent", "_recommendations")
            scenario_results[agent_key] = agent_result.current_message.content
            agent_display = agent_name.replace("Agent", "")
            print(f"🎯 {agent_display}: {agent_result.current_message.content[:80]}...")
        
        # Final orchestration
        orchestration_input = Message(role="user", content=f"""
        Orchestrate the final home automation response for scenario: {scenario}
        
        You have received these specialist recommendations:
        - Context: {scenario_results["context_analysis"]}
        - Lighting: {scenario_results["lighting_recommendations"]}
        - Climate: {scenario_results["climate_recommendations"]}
        - Security: {scenario_results["security_recommendations"]}
        - Energy: {scenario_results["energy_recommendations"]}
        - Appliances: {scenario_results["appliance_recommendations"]}
        
        Provide coordinated final instructions that balance all considerations.
        """)
        
        orchestration_result = await rt.call_agent("HomeOrchestrator", orchestration_input)
        scenario_results["final_orchestration"] = orchestration_result.current_message.content
        print(f"🏠 Orchestrator: {orchestration_result.current_message.content[:100]}...")
    
    return scenario_results

# ===== DEMO FUNCTIONS =====

async def demo_morning_routine():
    """Demonstrate morning routine automation."""
    print("🌅 Morning Routine Automation Demo")
    print("=" * 50)
    
    home_state = HomeState(
        occupied_rooms=["bedroom"],
        current_temperature=68.0,
        target_temperature=71.0,
        security_status="armed_home",
        energy_usage=2.1,
        time_of_day="early_morning",
        weather_outside="sunny, 45°F",
        resident_preferences={
            "morning_temp": "71°F",
            "wake_time": "7:00 AM",
            "coffee_ready": "7:15 AM"
        }
    )
    
    scenario = "Resident is waking up, need to prepare home for morning routine"
    await execute_home_automation_scenario(scenario, home_state)

async def demo_evening_routine():
    """Demonstrate evening routine automation."""
    print("\n🌙 Evening Routine Automation Demo")
    print("=" * 50)
    
    home_state = HomeState(
        occupied_rooms=["living_room", "kitchen"],
        current_temperature=74.0,
        target_temperature=72.0,
        security_status="disarmed",
        energy_usage=5.8,
        time_of_day="evening",
        weather_outside="clear, 52°F",
        resident_preferences={
            "evening_temp": "70°F",
            "bedtime": "10:30 PM",
            "evening_lighting": "warm_dim"
        }
    )
    
    scenario = "Family is settling in for evening, prepare for nighttime routine"
    await execute_home_automation_scenario(scenario, home_state)

async def demo_energy_optimization():
    """Demonstrate energy optimization during peak hours."""
    print("\n⚡ Energy Optimization Demo")
    print("=" * 50)
    
    home_state = HomeState(
        occupied_rooms=["office"],
        current_temperature=75.0,
        target_temperature=73.0,
        security_status="disarmed",
        energy_usage=8.5,  # High usage
        time_of_day="afternoon_peak",
        weather_outside="hot, 85°F",
        resident_preferences={
            "max_energy_cost": "$3.00/hour",
            "comfort_priority": "medium"
        }
    )
    
    scenario = "Peak electricity rates in effect, optimize energy usage while maintaining comfort"
    await execute_home_automation_scenario(scenario, home_state)

async def demo_security_incident():
    """Demonstrate security incident response."""
    print("\n🚨 Security Incident Response Demo")
    print("=" * 50)
    
    home_state = HomeState(
        occupied_rooms=[],  # Nobody home
        current_temperature=71.0,
        target_temperature=68.0,  # Away mode
        security_status="armed_away",
        energy_usage=1.2,
        time_of_day="afternoon",
        weather_outside="overcast, 62°F",
        resident_preferences={
            "security_level": "high",
            "notification_method": "mobile_app"
        }
    )
    
    scenario = "Motion detected in living room while home is in away mode - potential security incident"
    await execute_home_automation_scenario(scenario, home_state)

async def demo_guest_mode():
    """Demonstrate automation adjustments for guests."""
    print("\n👥 Guest Mode Automation Demo")
    print("=" * 50)
    
    home_state = HomeState(
        occupied_rooms=["living_room", "guest_bedroom", "kitchen"],
        current_temperature=72.0,
        target_temperature=73.0,
        security_status="armed_home",
        energy_usage=6.2,
        time_of_day="evening",
        weather_outside="mild, 65°F",
        resident_preferences={
            "guest_comfort": "high_priority",
            "privacy_mode": "enabled"
        }
    )
    
    scenario = "Guests staying overnight, adjust home automation for comfort and privacy"
    await execute_home_automation_scenario(scenario, home_state)

async def demo_parallel_agent_consultation():
    """Demonstrate parallel consultation of multiple agents."""
    print("\n⚡ Parallel Agent Consultation Demo")
    print("=" * 50)
    
    scenario = "Optimize home systems for work-from-home day with video conferences"
    home_state = generate_sample_home_state()
    
    async with app.run_context() as rt:
        print(f"📝 Scenario: {scenario}")
        print(f"🏠 Consulting all agents simultaneously...")
        
        # Parallel consultation
        agents = ["LightingAgent", "ClimateAgent", "EnergyAgent", "SecurityAgent"]
        input_msg = Message(role="user", content=f"Optimize for scenario: {scenario}")
        
        tasks = []
        for agent in agents:
            task = rt.call_agent(agent, input_msg)
            tasks.append((agent, task))
        
        # Collect results
        print("\n🎯 Agent Recommendations:")
        for agent, task in tasks:
            result = await task
            agent_name = agent.replace("Agent", "")
            print(f"   {agent_name}: {result.current_message.content[:60]}...")

async def demo_interactive_home_control():
    """Interactive home control interface."""
    print("\n💬 Interactive Smart Home Control")
    print("=" * 50)
    print("Describe a home automation scenario or ask for recommendations!")
    print("Type 'quit' to exit.\n")
    
    home_state = generate_sample_home_state()
    
    async with app.run_context() as rt:
        while True:
            user_input = input("🏠 Home Command: ").strip()
            if user_input.lower() in ['quit', 'exit', 'q']:
                break
                
            if not user_input:
                continue
            
            try:
                # Route to orchestrator for intelligent handling
                home_input = Message(role="user", content=f"""
                Home automation request: {user_input}
                
                Current home state:
                - Occupied rooms: {home_state.occupied_rooms}
                - Temperature: {home_state.current_temperature}°F
                - Time: {home_state.time_of_day}
                - Weather: {home_state.weather_outside}
                - Security: {home_state.security_status}
                
                Provide intelligent home automation response.
                """)
                
                result = await rt.call_agent("HomeOrchestrator", home_input)
                print(f"🏠 System: {result.current_message.content}\n")
                
            except Exception as e:
                print(f"❌ Error: {e}\n")

# ===== MAIN DEMO =====

async def main():
    """Main demo function with user choices."""
    print("🏠 TFrameX Smart Home Orchestration")
    print("=" * 50)
    print("This advanced example demonstrates intelligent home")
    print("automation using coordinated multi-agent systems")
    print("for lighting, climate, security, and energy management.\n")
    
    while True:
        print("Choose a demo:")
        print("1. 🌅 Morning Routine Automation")
        print("2. 🌙 Evening Routine Automation") 
        print("3. ⚡ Energy Optimization Demo")
        print("4. 🚨 Security Incident Response")
        print("5. 👥 Guest Mode Automation")
        print("6. ⚡ Parallel Agent Consultation")
        print("7. 💬 Interactive Home Control")
        print("8. ❌ Exit")
        
        choice = input("\nEnter your choice (1-8): ").strip()
        
        if choice == "1":
            await demo_morning_routine()
        elif choice == "2":
            await demo_evening_routine()
        elif choice == "3":
            await demo_energy_optimization()
        elif choice == "4":
            await demo_security_incident()
        elif choice == "5":
            await demo_guest_mode()
        elif choice == "6":
            await demo_parallel_agent_consultation()
        elif choice == "7":
            await demo_interactive_home_control()
        elif choice == "8":
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice. Please try again.\n")

if __name__ == "__main__":
    asyncio.run(main())