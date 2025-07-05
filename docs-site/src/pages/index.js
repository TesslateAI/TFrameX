import React from 'react';
import clsx from 'clsx';
import Link from '@docusaurus/Link';
import useDocusaurusContext from '@docusaurus/useDocusaurusContext';
import Layout from '@theme/Layout';
import HomepageFeatures from '@site/src/components/HomepageFeatures';

import styles from './index.module.css';

function HomepageHeader() {
  const {siteConfig} = useDocusaurusContext();
  return (
    <header className={clsx('hero hero--primary', styles.heroBanner)}>
      <div className="container">
        <h1 className="hero__title animate-fade-in-up">
          {siteConfig.title}
          <span className="version-badge">v1.1.0</span>
        </h1>
        <p className="hero__subtitle animate-fade-in-up">{siteConfig.tagline}</p>
        <div className={clsx(styles.buttons, 'animate-fade-in-up')}>
          <Link
            className="button button--secondary button--lg"
            to="/docs/intro">
            Get Started - 5min ⏱️
          </Link>
          <Link
            className="button button--primary button--lg margin-left--md"
            to="/docs/quickstart">
            Quick Start 🚀
          </Link>
        </div>
        <div className="margin-top--lg animate-fade-in-up">
          <code className="cli-command">pip install tframex</code>
        </div>
      </div>
    </header>
  );
}

export default function Home() {
  const {siteConfig} = useDocusaurusContext();
  return (
    <Layout
      title={`${siteConfig.title} - Build Sophisticated AI Agent Systems`}
      description="TFrameX is a production-ready Python framework for building sophisticated multi-agent LLM applications with powerful orchestration, enterprise features, and CLI tooling.">
      <HomepageHeader />
      <main>
        <HomepageFeatures />
        
        {/* New in v1.1.0 Section */}
        <section className="landing-section">
          <div className="container">
            <h2 className="section-title">🎉 New in v1.1.0</h2>
            <div className="row">
              <div className="col col--4">
                <div className="feature">
                  <h3>⚡ CLI Tooling</h3>
                  <p>Complete command-line interface with <code>tframex basic</code>, <code>tframex setup</code>, and <code>tframex serve</code> commands.</p>
                </div>
              </div>
              <div className="col col--4">
                <div className="feature">
                  <h3>🔌 Enhanced MCP</h3>
                  <p>Improved Model Context Protocol integration with better stability, performance, and error handling.</p>
                </div>
              </div>
              <div className="col col--4">
                <div className="feature">
                  <h3>🏢 Enterprise Ready</h3>
                  <p>Comprehensive enterprise features including RBAC, metrics, audit logging, and multi-backend storage.</p>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Quick Examples Section */}
        <section className="landing-section">
          <div className="container">
            <h2 className="section-title">Get Started in Seconds</h2>
            <div className="row">
              <div className="col col--6">
                <h3>1. Install TFrameX</h3>
                <pre className="language-bash">
                  <code>pip install tframex</code>
                </pre>
              </div>
              <div className="col col--6">
                <h3>2. Start Interactive Session</h3>
                <pre className="language-bash">
                  <code>export OPENAI_API_KEY="sk-..."
tframex basic</code>
                </pre>
              </div>
            </div>
            <div className="row margin-top--lg">
              <div className="col col--6">
                <h3>3. Create a Project</h3>
                <pre className="language-bash">
                  <code>tframex setup my-assistant
cd my-assistant
python main.py</code>
                </pre>
              </div>
              <div className="col col--6">
                <h3>4. Launch Web Interface</h3>
                <pre className="language-bash">
                  <code>pip install tframex[web]
tframex serve</code>
                </pre>
              </div>
            </div>
          </div>
        </section>

        {/* Use Cases Section */}
        <section className="landing-section">
          <div className="container">
            <h2 className="section-title">Build Production AI Systems</h2>
            <div className="row">
              <div className="col col--4">
                <div className="feature">
                  <h3>🤝 Customer Service</h3>
                  <p>Multi-tier support systems with intelligent routing, escalation workflows, and knowledge base integration.</p>
                </div>
              </div>
              <div className="col col--4">
                <div className="feature">
                  <h3>📊 Data Analysis</h3>
                  <p>Collaborative analysis with specialized agents for statistics, visualization, and business insights.</p>
                </div>
              </div>
              <div className="col col--4">
                <div className="feature">
                  <h3>📝 Content Creation</h3>
                  <p>End-to-end pipelines with research, writing, editing, and SEO optimization agents.</p>
                </div>
              </div>
              <div className="col col--4">
                <div className="feature">
                  <h3>🏭 DevOps Automation</h3>
                  <p>Infrastructure management with approval workflows, monitoring integration, and incident response.</p>
                </div>
              </div>
              <div className="col col--4">
                <div className="feature">
                  <h3>💼 Financial Analysis</h3>
                  <p>Trading systems with risk management, compliance checking, and portfolio optimization.</p>
                </div>
              </div>
              <div className="col col--4">
                <div className="feature">
                  <h3>🏥 Healthcare Support</h3>
                  <p>Diagnostic assistance with specialist consultation patterns and regulatory compliance.</p>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Architecture Preview */}
        <section className="landing-section">
          <div className="container">
            <h2 className="section-title">Clean, Extensible Architecture</h2>
            <div className="text--center">
              <img 
                src="/img/01-overall-framework-architecture.png" 
                alt="TFrameX Architecture"
                style={{maxWidth: '800px', width: '100%'}}
              />
            </div>
            <div className="row margin-top--lg">
              <div className="col col--6">
                <h3>🧩 Modular Design</h3>
                <ul>
                  <li>Composable agents, tools, and flows</li>
                  <li>Plugin architecture for extensions</li>
                  <li>Clean separation of concerns</li>
                </ul>
              </div>
              <div className="col col--6">
                <h3>🚀 Production Ready</h3>
                <ul>
                  <li>Async-first for performance</li>
                  <li>Comprehensive error handling</li>
                  <li>Enterprise security features</li>
                </ul>
              </div>
            </div>
          </div>
        </section>

        {/* Code Example */}
        <section className="landing-section">
          <div className="container">
            <h2 className="section-title">Simple Yet Powerful</h2>
            <pre className="language-python">
              <code>{`from tframex import TFrameXApp
from tframex.agents.llm_agent import LLMAgent
from tframex.util.llms import OpenAIChatLLM
import asyncio

app = TFrameXApp()

# Define a tool
@app.tool(description="Search the web for information")
async def web_search(query: str) -> str:
    # Your implementation here
    return f"Results for: {query}"

# Create an agent
assistant = LLMAgent(
    name="ResearchAssistant",
    description="AI research assistant",
    llm=OpenAIChatLLM(),
    tools=["web_search"],
    system_prompt="You are a helpful research assistant."
)

app.register_agent(assistant)

# Run the agent
async def main():
    async with app.run_context() as rt:
        response = await rt.call_agent(
            "ResearchAssistant", 
            "Find information about quantum computing"
        )
        print(response)

asyncio.run(main())`}</code>
            </pre>
          </div>
        </section>

        {/* CTA Section */}
        <section className="landing-section" style={{backgroundColor: 'var(--ifm-color-primary)', color: 'white'}}>
          <div className="container text--center">
            <h2 style={{color: 'white', marginBottom: '2rem'}}>Ready to Build Intelligent AI Systems?</h2>
            <div className={styles.buttons}>
              <Link
                className="button button--secondary button--lg"
                to="/docs/intro"
                style={{marginRight: '1rem'}}>
                Read Documentation
              </Link>
              <Link
                className="button button--outline button--secondary button--lg"
                to="https://github.com/TesslateAI/TFrameX">
                View on GitHub
              </Link>
            </div>
          </div>
        </section>
      </main>
    </Layout>
  );
}