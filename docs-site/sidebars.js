/**
 * Creating a sidebar enables you to:
 - create an ordered group of docs
 - render a sidebar for each doc of that group
 - provide next/previous navigation

 The sidebars can be generated from the filesystem, or explicitly defined here.

 Create as many sidebars as you want.
 */

// @ts-check

/** @type {import('@docusaurus/plugin-content-docs').SidebarsConfig} */
const sidebars = {
  // By default, Docusaurus generates a sidebar from the docs folder structure
  tutorialSidebar: [
    {
      type: 'doc',
      id: 'intro',
      label: 'Introduction',
    },
    {
      type: 'category',
      label: 'Getting Started',
      items: [
        'installation',
        'quickstart',
        'first-agent',
      ],
    },
    {
      type: 'category',
      label: 'Core Concepts',
      items: [
        'concepts/overview',
        'concepts/agents',
        'concepts/tools',
        'concepts/flows',
        'concepts/patterns',
        'concepts/memory',
        'concepts/mcp-integration',
      ],
    },
    {
      type: 'category',
      label: 'CLI Reference',
      items: [
        'cli/overview',
        'cli/commands',
        'cli/basic',
        'cli/setup',
        'cli/serve',
      ],
    },
    {
      type: 'category',
      label: 'API Reference',
      items: [
        'api/overview',
        'api/tframexapp',
        'api/agents',
        'api/tools',
        'api/flows',
        'api/patterns',
        'api/mcp',
        'api/memory',
      ],
    },
    {
      type: 'category',
      label: 'Enterprise Features',
      items: [
        'enterprise/overview',
        'enterprise/configuration',
        {
          type: 'category',
          label: 'Security',
          items: [
            'enterprise/security/overview',
            'enterprise/security/authentication',
            'enterprise/security/authorization',
            'enterprise/security/audit',
            'enterprise/security/sessions',
          ],
        },
        'enterprise/metrics',
      ],
    },
  ],
};

module.exports = sidebars;