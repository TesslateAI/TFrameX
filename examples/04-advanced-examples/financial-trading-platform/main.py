#!/usr/bin/env python3
"""
TFrameX Financial Trading Platform - Advanced Example

Demonstrates a sophisticated financial trading system using TFrameX's multi-agent
architecture. Multiple specialized agents work together to analyze markets,
manage risk, execute trades, and optimize portfolios while maintaining strict
risk controls and regulatory compliance.

Platform Features:
- Multi-asset market analysis and trading
- Real-time risk assessment and management
- Algorithmic trading strategy coordination
- Portfolio optimization and rebalancing
- Regulatory compliance monitoring
- Performance analytics and reporting

IMPORTANT DISCLAIMER:
This is a demonstration example for educational purposes only.
This is NOT real trading software and should not be used for actual financial trading.
Always consult with qualified financial professionals before making investment decisions.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from decimal import Decimal
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

# ===== FINANCIAL DATA MODELS =====

class AssetType(Enum):
    STOCK = "stock"
    BOND = "bond"
    CRYPTO = "crypto"
    FOREX = "forex"
    COMMODITY = "commodity"
    ETF = "etf"

class OrderType(Enum):
    MARKET = "market"
    LIMIT = "limit"
    STOP_LOSS = "stop_loss"
    STOP_LIMIT = "stop_limit"

class RiskLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class MarketData:
    """Real-time market data for an asset."""
    symbol: str
    price: Decimal
    volume: int
    change_percent: float
    bid: Decimal
    ask: Decimal
    timestamp: datetime

@dataclass
class Position:
    """Trading position information."""
    symbol: str
    quantity: int
    entry_price: Decimal
    current_price: Decimal
    unrealized_pnl: Decimal
    asset_type: AssetType

@dataclass
class TradingSignal:
    """Trading signal from analysis agents."""
    symbol: str
    action: str  # BUY, SELL, HOLD
    confidence: float
    price_target: Optional[Decimal]
    stop_loss: Optional[Decimal]
    reasoning: str
    agent_source: str

# ===== TRADING AGENTS =====

@app.agent(
    name="TradingOrchestrator",
    description="Central coordinator for all trading operations and risk management",
    system_prompt="""
    You are the central trading orchestrator responsible for:
    
    1. **Trading Coordination**: Coordinate all trading activities and agent recommendations
    2. **Risk Management**: Ensure all trades comply with risk limits and guidelines
    3. **Portfolio Strategy**: Maintain overall portfolio strategy and allocation targets
    4. **Conflict Resolution**: Resolve conflicts between different agent recommendations
    5. **Regulatory Compliance**: Ensure all activities comply with trading regulations
    
    TRADING PRINCIPLES:
    - Risk management is the top priority
    - Never exceed position size limits or risk parameters
    - Maintain diversification across asset classes
    - Consider market conditions and volatility
    - Always validate trades against compliance rules
    
    IMPORTANT: This is a simulation for educational purposes only.
    All recommendations should be clearly marked as educational examples.
    """
)
async def trading_orchestrator():
    """Central coordinator for all trading operations."""
    pass

@app.agent(
    name="MarketAnalyst",
    description="Analyzes market trends, technical indicators, and price movements",
    system_prompt="""
    You are a senior market analyst specializing in:
    
    1. **Technical Analysis**: Chart patterns, indicators, and price action analysis
    2. **Market Trends**: Identify short-term and long-term market trends
    3. **Volatility Assessment**: Analyze market volatility and its implications
    4. **Momentum Analysis**: Identify momentum shifts and trend changes
    5. **Support/Resistance**: Identify key support and resistance levels
    
    ANALYSIS APPROACH:
    - Use multiple timeframes for comprehensive analysis
    - Consider volume patterns and market breadth
    - Identify potential breakout and breakdown scenarios
    - Assess market sentiment and investor behavior
    - Provide clear, actionable insights
    
    Focus on providing objective, data-driven market analysis.
    Always include confidence levels and risk considerations in your analysis.
    """
)
async def market_analyst():
    """Analyzes market trends and technical indicators."""
    pass

@app.agent(
    name="FundamentalAnalyst",
    description="Analyzes company fundamentals, economic data, and valuation metrics",
    system_prompt="""
    You are a fundamental analyst specializing in:
    
    1. **Company Analysis**: Financial statements, earnings, and business fundamentals
    2. **Economic Analysis**: Macroeconomic factors and their market impact
    3. **Valuation Assessment**: Fair value estimation and valuation metrics
    4. **Industry Analysis**: Sector trends and competitive positioning
    5. **News Impact**: Analysis of news events and their market implications
    
    ANALYSIS FOCUS:
    - Evaluate long-term investment value and growth prospects
    - Assess financial health and business model sustainability
    - Consider macroeconomic trends and policy impacts
    - Analyze competitive advantages and market position
    - Provide fair value estimates with supporting rationale
    
    Provide thorough fundamental analysis with clear investment thesis.
    Consider both upside potential and downside risks.
    """
)
async def fundamental_analyst():
    """Analyzes company fundamentals and economic data."""
    pass

@app.agent(
    name="RiskManager",
    description="Monitors and manages trading risk across all positions and strategies",
    system_prompt="""
    You are the risk management specialist responsible for:
    
    1. **Position Risk**: Monitor individual position sizes and concentration risk
    2. **Portfolio Risk**: Assess overall portfolio risk and correlation
    3. **Market Risk**: Evaluate market exposure and volatility impact
    4. **Liquidity Risk**: Ensure adequate liquidity for position management
    5. **Compliance Risk**: Verify compliance with trading rules and regulations
    
    RISK MANAGEMENT PRINCIPLES:
    - Never allow positions to exceed maximum risk limits
    - Maintain appropriate diversification across assets and sectors
    - Monitor correlation risk and avoid concentration
    - Ensure stop-loss levels are appropriate and respected
    - Alert to any regulatory or compliance violations
    
    RISK LIMITS:
    - Maximum single position: 5% of portfolio
    - Maximum sector concentration: 20% of portfolio
    - Maximum daily loss limit: 2% of portfolio
    - Minimum cash reserve: 10% of portfolio
    
    Provide clear risk assessments and immediate alerts for any limit violations.
    """
)
async def risk_manager():
    """Monitors and manages all trading risks."""
    pass

@app.agent(
    name="AlgorithmicTrader",
    description="Executes algorithmic trading strategies and order management",
    system_prompt="""
    You are an algorithmic trading specialist focused on:
    
    1. **Strategy Execution**: Implement and execute algorithmic trading strategies
    2. **Order Management**: Optimize trade execution and minimize market impact
    3. **Timing Optimization**: Determine optimal entry and exit timing
    4. **Liquidity Management**: Ensure efficient order execution across markets
    5. **Performance Tracking**: Monitor strategy performance and efficiency
    
    EXECUTION PRINCIPLES:
    - Minimize market impact and slippage
    - Use appropriate order types for different market conditions
    - Consider liquidity and volume patterns for timing
    - Implement proper position sizing and risk controls
    - Track execution quality and performance metrics
    
    STRATEGY TYPES:
    - Trend following strategies
    - Mean reversion strategies  
    - Momentum strategies
    - Arbitrage opportunities
    - Market making strategies
    
    Focus on efficient execution while maintaining strict risk controls.
    """
)
async def algorithmic_trader():
    """Executes algorithmic trading strategies."""
    pass

@app.agent(
    name="PortfolioManager",
    description="Manages portfolio allocation, rebalancing, and optimization",
    system_prompt="""
    You are a portfolio manager responsible for:
    
    1. **Asset Allocation**: Determine optimal allocation across asset classes
    2. **Portfolio Rebalancing**: Maintain target allocations and risk levels
    3. **Diversification**: Ensure appropriate diversification across holdings
    4. **Performance Optimization**: Optimize risk-adjusted returns
    5. **Strategic Planning**: Long-term portfolio strategy and objectives
    
    PORTFOLIO PRINCIPLES:
    - Maintain strategic asset allocation targets
    - Balance risk and return objectives
    - Consider correlation and diversification benefits
    - Implement tactical adjustments based on market conditions
    - Monitor and control overall portfolio risk
    
    TARGET ALLOCATIONS (example):
    - Equities: 60-70%
    - Bonds: 20-30%
    - Alternatives: 5-15%
    - Cash: 5-10%
    
    Provide portfolio recommendations that balance growth and risk management.
    """
)
async def portfolio_manager():
    """Manages portfolio allocation and optimization."""
    pass

@app.agent(
    name="SentimentAnalyst",
    description="Analyzes market sentiment, news, and social media trends",
    system_prompt="""
    You are a sentiment analysis specialist focused on:
    
    1. **Market Sentiment**: Gauge overall market mood and investor sentiment
    2. **News Analysis**: Analyze news impact on asset prices and market trends
    3. **Social Media Trends**: Monitor social media for market-moving sentiment
    4. **Fear/Greed Indicators**: Track sentiment indicators and contrarian signals
    5. **Event Impact**: Assess potential impact of upcoming events and announcements
    
    SENTIMENT INDICATORS:
    - VIX and volatility measures
    - Put/call ratios and options sentiment
    - Insider trading activity
    - Social media sentiment scores
    - News sentiment and keyword analysis
    
    ANALYSIS APPROACH:
    - Identify sentiment extremes that may signal reversals
    - Track sentiment momentum and changes
    - Consider sentiment in context of technical and fundamental analysis
    - Provide contrarian and momentum perspectives
    - Assess crowd psychology and behavioral factors
    
    Provide sentiment insights that complement technical and fundamental analysis.
    """
)
async def sentiment_analyst():
    """Analyzes market sentiment and behavioral indicators."""
    pass

# ===== TRADING FLOWS =====

# Market analysis flow
market_analysis_flow = Flow(
    flow_name="MarketAnalysisFlow",
    description="Comprehensive market analysis combining multiple perspectives"
)
market_analysis_flow.add_step("MarketAnalyst")        # Technical analysis
market_analysis_flow.add_step("FundamentalAnalyst")   # Fundamental analysis  
market_analysis_flow.add_step("SentimentAnalyst")     # Sentiment analysis
market_analysis_flow.add_step("TradingOrchestrator")  # Synthesis

# Trade evaluation flow
trade_evaluation_flow = Flow(
    flow_name="TradeEvaluationFlow", 
    description="Evaluate and validate potential trades"
)
trade_evaluation_flow.add_step("RiskManager")         # Risk assessment
trade_evaluation_flow.add_step("PortfolioManager")    # Portfolio impact
trade_evaluation_flow.add_step("AlgorithmicTrader")   # Execution planning
trade_evaluation_flow.add_step("TradingOrchestrator") # Final decision

# Portfolio review flow
portfolio_review_flow = Flow(
    flow_name="PortfolioReviewFlow",
    description="Comprehensive portfolio analysis and rebalancing"
)
portfolio_review_flow.add_step("PortfolioManager")    # Portfolio analysis
portfolio_review_flow.add_step("RiskManager")         # Risk review
portfolio_review_flow.add_step("MarketAnalyst")       # Market context
portfolio_review_flow.add_step("TradingOrchestrator") # Rebalancing decisions

# Register flows
app.register_flow(market_analysis_flow)
app.register_flow(trade_evaluation_flow)
app.register_flow(portfolio_review_flow)

# ===== SAMPLE DATA GENERATION =====

def generate_sample_market_data() -> Dict[str, MarketData]:
    """Generate sample market data for demonstration."""
    return {
        "AAPL": MarketData("AAPL", Decimal("175.50"), 1000000, 2.1, Decimal("175.45"), Decimal("175.55"), datetime.now()),
        "GOOGL": MarketData("GOOGL", Decimal("142.30"), 800000, -0.8, Decimal("142.25"), Decimal("142.35"), datetime.now()),
        "TSLA": MarketData("TSLA", Decimal("248.75"), 1500000, 3.2, Decimal("248.70"), Decimal("248.80"), datetime.now()),
        "MSFT": MarketData("MSFT", Decimal("378.90"), 900000, 1.5, Decimal("378.85"), Decimal("378.95"), datetime.now()),
        "SPY": MarketData("SPY", Decimal("485.20"), 2000000, 0.9, Decimal("485.15"), Decimal("485.25"), datetime.now()),
    }

def generate_sample_portfolio() -> Dict[str, Position]:
    """Generate sample portfolio positions."""
    return {
        "AAPL": Position("AAPL", 100, Decimal("170.00"), Decimal("175.50"), Decimal("550.00"), AssetType.STOCK),
        "GOOGL": Position("GOOGL", 50, Decimal("145.00"), Decimal("142.30"), Decimal("-135.00"), AssetType.STOCK),
        "SPY": Position("SPY", 200, Decimal("480.00"), Decimal("485.20"), Decimal("1040.00"), AssetType.ETF),
    }

# ===== SIMULATION FUNCTIONS =====

async def execute_market_analysis(symbols: List[str]) -> Dict:
    """Execute comprehensive market analysis for given symbols."""
    
    print(f"📊 Market Analysis for: {', '.join(symbols)}")
    print("=" * 60)
    
    analysis_results = {}
    market_data = generate_sample_market_data()
    
    async with app.run_context() as rt:
        for symbol in symbols:
            if symbol not in market_data:
                continue
                
            data = market_data[symbol]
            print(f"\n🔍 Analyzing {symbol} - ${data.price} ({data.change_percent:+.1f}%)")
            
            analysis_context = f"""
            Analyze {symbol} with the following market data:
            - Current Price: ${data.price}
            - Daily Change: {data.change_percent:+.1f}%
            - Volume: {data.volume:,}
            - Bid/Ask: ${data.bid}/${data.ask}
            
            Provide your specialized analysis for this asset.
            """
            
            # Parallel analysis by specialists
            analysis_tasks = [
                ("MarketAnalyst", "technical_analysis"),
                ("FundamentalAnalyst", "fundamental_analysis"),
                ("SentimentAnalyst", "sentiment_analysis")
            ]
            
            symbol_analysis = {}
            for agent_name, analysis_type in analysis_tasks:
                input_msg = Message(role="user", content=analysis_context)
                result = await rt.call_agent(agent_name, input_msg)
                symbol_analysis[analysis_type] = result.current_message.content
                agent_display = agent_name.replace("Analyst", "")
                print(f"   📈 {agent_display}: {result.current_message.content[:60]}...")
            
            # Orchestrator synthesis
            synthesis_input = Message(role="user", content=f"""
            Synthesize the analysis for {symbol}:
            
            Technical Analysis: {symbol_analysis['technical_analysis']}
            Fundamental Analysis: {symbol_analysis['fundamental_analysis']}
            Sentiment Analysis: {symbol_analysis['sentiment_analysis']}
            
            Provide overall trading recommendation and rationale.
            """)
            
            synthesis_result = await rt.call_agent("TradingOrchestrator", synthesis_input)
            symbol_analysis["trading_recommendation"] = synthesis_result.current_message.content
            print(f"   🎯 Recommendation: {synthesis_result.current_message.content[:80]}...")
            
            analysis_results[symbol] = symbol_analysis
    
    return analysis_results

async def execute_trade_evaluation(trade_request: str) -> Dict:
    """Evaluate a potential trade through the risk management process."""
    
    print(f"⚖️ Trade Evaluation: {trade_request}")
    print("=" * 50)
    
    evaluation_results = {}
    portfolio = generate_sample_portfolio()
    
    async with app.run_context() as rt:
        # Risk assessment
        print("\n🛡️ Risk Assessment")
        risk_input = Message(role="user", content=f"""
        Evaluate the risk for this trade request: {trade_request}
        
        Current portfolio positions:
        {json.dumps({k: f"{v.symbol}: {v.quantity} shares @ ${v.entry_price}" for k, v in portfolio.items()}, indent=2)}
        
        Assess position sizing, portfolio impact, and risk compliance.
        """)
        
        risk_result = await rt.call_agent("RiskManager", risk_input)
        evaluation_results["risk_assessment"] = risk_result.current_message.content
        print(f"   Risk: {risk_result.current_message.content[:80]}...")
        
        # Portfolio impact analysis  
        print("\n📊 Portfolio Impact Analysis")
        portfolio_input = Message(role="user", content=f"""
        Analyze portfolio impact for: {trade_request}
        
        Current portfolio allocation and the proposed trade's impact on diversification,
        sector exposure, and strategic allocation targets.
        """)
        
        portfolio_result = await rt.call_agent("PortfolioManager", portfolio_input)
        evaluation_results["portfolio_impact"] = portfolio_result.current_message.content
        print(f"   Portfolio: {portfolio_result.current_message.content[:80]}...")
        
        # Execution planning
        print("\n⚡ Execution Planning")
        execution_input = Message(role="user", content=f"""
        Plan execution strategy for: {trade_request}
        
        Consider optimal timing, order types, and execution methodology
        to minimize market impact and maximize efficiency.
        """)
        
        execution_result = await rt.call_agent("AlgorithmicTrader", execution_input)
        evaluation_results["execution_plan"] = execution_result.current_message.content
        print(f"   Execution: {execution_result.current_message.content[:80]}...")
        
        # Final orchestration decision
        print("\n🎯 Final Trading Decision")
        decision_input = Message(role="user", content=f"""
        Make final trading decision for: {trade_request}
        
        Risk Assessment: {evaluation_results['risk_assessment']}
        Portfolio Impact: {evaluation_results['portfolio_impact']}
        Execution Plan: {evaluation_results['execution_plan']}
        
        Approve, modify, or reject the trade with clear rationale.
        """)
        
        decision_result = await rt.call_agent("TradingOrchestrator", decision_input)
        evaluation_results["final_decision"] = decision_result.current_message.content
        print(f"   Decision: {decision_result.current_message.content[:80]}...")
    
    return evaluation_results

# ===== DEMO FUNCTIONS =====

async def demo_market_analysis():
    """Demonstrate comprehensive market analysis."""
    print("📊 Market Analysis Demo")
    print("=" * 50)
    
    symbols = ["AAPL", "GOOGL", "TSLA"]
    await execute_market_analysis(symbols)

async def demo_trade_evaluation():
    """Demonstrate trade evaluation process."""
    print("\n⚖️ Trade Evaluation Demo")
    print("=" * 50)
    
    trade_request = "Buy 50 shares of NVDA at market price"
    await execute_trade_evaluation(trade_request)

async def demo_portfolio_review():
    """Demonstrate portfolio review and rebalancing."""
    print("\n📊 Portfolio Review Demo")
    print("=" * 50)
    
    portfolio = generate_sample_portfolio()
    
    async with app.run_context() as rt:
        print("📋 Current Portfolio:")
        for symbol, position in portfolio.items():
            pnl_color = "🟢" if position.unrealized_pnl > 0 else "🔴"
            print(f"   {symbol}: {position.quantity} shares @ ${position.entry_price} "
                  f"(Current: ${position.current_price}) {pnl_color} ${position.unrealized_pnl}")
        
        # Portfolio analysis
        portfolio_input = Message(role="user", content=f"""
        Review and analyze the current portfolio:
        
        Positions:
        {json.dumps({k: f"{v.quantity} shares of {v.symbol} @ ${v.entry_price}, current ${v.current_price}, P&L ${v.unrealized_pnl}" for k, v in portfolio.items()}, indent=2)}
        
        Assess allocation, performance, and recommend any rebalancing actions.
        """)
        
        portfolio_result = await rt.call_agent("PortfolioManager", portfolio_input)
        print(f"\n📊 Portfolio Analysis: {portfolio_result.current_message.content}")

async def demo_risk_monitoring():
    """Demonstrate real-time risk monitoring."""
    print("\n🛡️ Risk Monitoring Demo")
    print("=" * 50)
    
    portfolio = generate_sample_portfolio()
    
    async with app.run_context() as rt:
        # Simulate risk scenarios
        risk_scenarios = [
            "Market volatility spike - VIX up 25%",
            "Single position (AAPL) down 8% in one day",
            "Sector concentration risk - Tech positions correlated"
        ]
        
        for scenario in risk_scenarios:
            print(f"\n⚠️ Risk Scenario: {scenario}")
            
            risk_input = Message(role="user", content=f"""
            Assess risk impact for scenario: {scenario}
            
            Current portfolio:
            {json.dumps({k: f"{v.symbol}: {v.quantity} shares" for k, v in portfolio.items()}, indent=2)}
            
            Provide risk assessment and recommended actions.
            """)
            
            risk_result = await rt.call_agent("RiskManager", risk_input)
            print(f"   Risk Assessment: {risk_result.current_message.content[:100]}...")

async def demo_algorithmic_strategies():
    """Demonstrate algorithmic trading strategies."""
    print("\n⚡ Algorithmic Trading Strategies Demo")
    print("=" * 50)
    
    strategies = [
        "Momentum strategy - Buy stocks with strong upward momentum",
        "Mean reversion - Buy oversold stocks near support levels", 
        "Pairs trading - Long AAPL, short GOOGL on relative value"
    ]
    
    async with app.run_context() as rt:
        for strategy in strategies:
            print(f"\n🤖 Strategy: {strategy}")
            
            strategy_input = Message(role="user", content=f"""
            Implement algorithmic strategy: {strategy}
            
            Provide execution plan including:
            - Entry/exit criteria
            - Position sizing
            - Risk controls  
            - Performance metrics
            """)
            
            strategy_result = await rt.call_agent("AlgorithmicTrader", strategy_input)
            print(f"   Implementation: {strategy_result.current_message.content[:100]}...")

async def demo_parallel_analysis():
    """Demonstrate parallel analysis across multiple agents."""
    print("\n⚡ Parallel Analysis Demo")
    print("=" * 50)
    
    symbol = "SPY"
    market_data = generate_sample_market_data()[symbol]
    
    async with app.run_context() as rt:
        print(f"📊 Parallel Analysis for {symbol}")
        print(f"💰 Price: ${market_data.price} ({market_data.change_percent:+.1f}%)")
        
        # Parallel analysis by all agents
        agents = [
            "MarketAnalyst",
            "FundamentalAnalyst", 
            "SentimentAnalyst",
            "RiskManager",
            "PortfolioManager"
        ]
        
        analysis_input = Message(role="user", content=f"Analyze {symbol} from your perspective")
        
        tasks = []
        for agent in agents:
            task = rt.call_agent(agent, analysis_input)
            tasks.append((agent, task))
        
        print("\n🎯 Agent Perspectives:")
        for agent, task in tasks:
            result = await task
            agent_name = agent.replace("Manager", "").replace("Analyst", "")
            print(f"   {agent_name}: {result.current_message.content[:70]}...")

async def demo_interactive_trading():
    """Interactive trading interface."""
    print("\n💬 Interactive Trading Interface")
    print("=" * 50)
    print("Ask about market analysis, trading strategies, or portfolio management!")
    print("Type 'quit' to exit.\n")
    
    async with app.run_context() as rt:
        while True:
            user_input = input("💹 Trading Query: ").strip()
            if user_input.lower() in ['quit', 'exit', 'q']:
                break
                
            if not user_input:
                continue
            
            try:
                # Route to orchestrator for intelligent handling
                trading_input = Message(role="user", content=f"""
                Trading platform query: {user_input}
                
                Provide professional trading analysis or recommendation.
                Always include appropriate disclaimers for educational use only.
                """)
                
                result = await rt.call_agent("TradingOrchestrator", trading_input)
                print(f"🎯 Trading System: {result.current_message.content}\n")
                
            except Exception as e:
                print(f"❌ Error: {e}\n")

# ===== MAIN DEMO =====

async def main():
    """Main demo function with user choices."""
    print("💹 TFrameX Financial Trading Platform")
    print("=" * 50)
    print("⚠️  EDUCATIONAL SIMULATION ONLY - NOT FOR REAL TRADING")
    print("This example demonstrates multi-agent financial analysis")
    print("and trading coordination using TFrameX patterns.\n")
    
    while True:
        print("Choose a demo:")
        print("1. 📊 Market Analysis Demo")
        print("2. ⚖️ Trade Evaluation Demo")
        print("3. 📊 Portfolio Review Demo") 
        print("4. 🛡️ Risk Monitoring Demo")
        print("5. ⚡ Algorithmic Strategies Demo")
        print("6. ⚡ Parallel Analysis Demo")
        print("7. 💬 Interactive Trading Interface")
        print("8. ❌ Exit")
        
        choice = input("\nEnter your choice (1-8): ").strip()
        
        if choice == "1":
            await demo_market_analysis()
        elif choice == "2":
            await demo_trade_evaluation()
        elif choice == "3":
            await demo_portfolio_review()
        elif choice == "4":
            await demo_risk_monitoring()
        elif choice == "5":
            await demo_algorithmic_strategies()
        elif choice == "6":
            await demo_parallel_analysis()
        elif choice == "7":
            await demo_interactive_trading()
        elif choice == "8":
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice. Please try again.\n")

if __name__ == "__main__":
    print("\n⚠️  IMPORTANT DISCLAIMER:")
    print("This is a demonstration for educational purposes only.")
    print("This is NOT real trading software and should not be used for actual financial trading.")
    print("Always consult with qualified financial professionals before making investment decisions.\n")
    
    asyncio.run(main())