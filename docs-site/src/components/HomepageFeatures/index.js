import React from 'react';
import clsx from 'clsx';
import styles from './styles.module.css';

const FeatureList = [
  {
    title: '🧠 Intelligent Agents',
    description: (
      <>
        Define specialized agents with unique system prompts, tools, and LLM models. 
        Create hierarchical structures where supervisors delegate to specialists.
      </>
    ),
  },
  {
    title: '🛠️ Seamless Tool Integration',
    description: (
      <>
        Equip agents with custom tools using simple decorators. 
        Let them interact with APIs, databases, or any Python function.
      </>
    ),
  },
  {
    title: '🌊 Flow Orchestration',
    description: (
      <>
        Design complex workflows with Sequential, Parallel, Router, and Discussion patterns. 
        Chain agents and patterns for sophisticated automation.
      </>
    ),
  },
  {
    title: '🚀 Agent-as-Tool',
    description: (
      <>
        Enable agents to call other agents as tools, creating hierarchical 
        and supervised agent structures for complex reasoning.
      </>
    ),
  },
  {
    title: '🔌 MCP Integration',
    description: (
      <>
        Connect to external services via Model Context Protocol. 
        Access databases, APIs, and tools through a standardized interface.
      </>
    ),
  },
  {
    title: '⚡ CLI Tooling',
    description: (
      <>
        Complete command-line interface with instant sessions, 
        project scaffolding, and web deployment capabilities.
      </>
    ),
  },
];

function Feature({title, description}) {
  return (
    <div className={clsx('col col--4')}>
      <div className="text--center padding-horiz--md">
        <h3>{title}</h3>
        <p>{description}</p>
      </div>
    </div>
  );
}

export default function HomepageFeatures() {
  return (
    <section className={styles.features}>
      <div className="container">
        <div className="row">
          {FeatureList.map((props, idx) => (
            <Feature key={idx} {...props} />
          ))}
        </div>
      </div>
    </section>
  );
}