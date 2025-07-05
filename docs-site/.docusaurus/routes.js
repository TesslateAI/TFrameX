import React from 'react';
import ComponentCreator from '@docusaurus/ComponentCreator';

export default [
  {
    path: '/__docusaurus/debug',
    component: ComponentCreator('/__docusaurus/debug', '9a5'),
    exact: true
  },
  {
    path: '/__docusaurus/debug/config',
    component: ComponentCreator('/__docusaurus/debug/config', '57b'),
    exact: true
  },
  {
    path: '/__docusaurus/debug/content',
    component: ComponentCreator('/__docusaurus/debug/content', '4c6'),
    exact: true
  },
  {
    path: '/__docusaurus/debug/globalData',
    component: ComponentCreator('/__docusaurus/debug/globalData', '984'),
    exact: true
  },
  {
    path: '/__docusaurus/debug/metadata',
    component: ComponentCreator('/__docusaurus/debug/metadata', '275'),
    exact: true
  },
  {
    path: '/__docusaurus/debug/registry',
    component: ComponentCreator('/__docusaurus/debug/registry', 'd00'),
    exact: true
  },
  {
    path: '/__docusaurus/debug/routes',
    component: ComponentCreator('/__docusaurus/debug/routes', '0ed'),
    exact: true
  },
  {
    path: '/search',
    component: ComponentCreator('/search', 'a09'),
    exact: true
  },
  {
    path: '/docs',
    component: ComponentCreator('/docs', '262'),
    routes: [
      {
        path: '/docs',
        component: ComponentCreator('/docs', '730'),
        routes: [
          {
            path: '/docs',
            component: ComponentCreator('/docs', '486'),
            routes: [
              {
                path: '/docs/api/agents',
                component: ComponentCreator('/docs/api/agents', '2ab'),
                exact: true,
                sidebar: "tutorialSidebar"
              },
              {
                path: '/docs/api/flows',
                component: ComponentCreator('/docs/api/flows', 'e40'),
                exact: true,
                sidebar: "tutorialSidebar"
              },
              {
                path: '/docs/api/mcp',
                component: ComponentCreator('/docs/api/mcp', 'ad2'),
                exact: true,
                sidebar: "tutorialSidebar"
              },
              {
                path: '/docs/api/memory',
                component: ComponentCreator('/docs/api/memory', '806'),
                exact: true,
                sidebar: "tutorialSidebar"
              },
              {
                path: '/docs/api/overview',
                component: ComponentCreator('/docs/api/overview', '79e'),
                exact: true,
                sidebar: "tutorialSidebar"
              },
              {
                path: '/docs/api/patterns',
                component: ComponentCreator('/docs/api/patterns', '763'),
                exact: true,
                sidebar: "tutorialSidebar"
              },
              {
                path: '/docs/api/patterns_old',
                component: ComponentCreator('/docs/api/patterns_old', 'dac'),
                exact: true
              },
              {
                path: '/docs/api/tframexapp',
                component: ComponentCreator('/docs/api/tframexapp', '221'),
                exact: true,
                sidebar: "tutorialSidebar"
              },
              {
                path: '/docs/api/tools',
                component: ComponentCreator('/docs/api/tools', 'd23'),
                exact: true,
                sidebar: "tutorialSidebar"
              },
              {
                path: '/docs/cli/basic',
                component: ComponentCreator('/docs/cli/basic', '956'),
                exact: true,
                sidebar: "tutorialSidebar"
              },
              {
                path: '/docs/cli/commands',
                component: ComponentCreator('/docs/cli/commands', 'd7f'),
                exact: true,
                sidebar: "tutorialSidebar"
              },
              {
                path: '/docs/cli/overview',
                component: ComponentCreator('/docs/cli/overview', '128'),
                exact: true,
                sidebar: "tutorialSidebar"
              },
              {
                path: '/docs/cli/serve',
                component: ComponentCreator('/docs/cli/serve', 'e8a'),
                exact: true,
                sidebar: "tutorialSidebar"
              },
              {
                path: '/docs/cli/setup',
                component: ComponentCreator('/docs/cli/setup', 'cd0'),
                exact: true,
                sidebar: "tutorialSidebar"
              },
              {
                path: '/docs/concepts/agents',
                component: ComponentCreator('/docs/concepts/agents', '518'),
                exact: true,
                sidebar: "tutorialSidebar"
              },
              {
                path: '/docs/concepts/flows',
                component: ComponentCreator('/docs/concepts/flows', '199'),
                exact: true,
                sidebar: "tutorialSidebar"
              },
              {
                path: '/docs/concepts/mcp-integration',
                component: ComponentCreator('/docs/concepts/mcp-integration', 'f44'),
                exact: true,
                sidebar: "tutorialSidebar"
              },
              {
                path: '/docs/concepts/memory',
                component: ComponentCreator('/docs/concepts/memory', 'b59'),
                exact: true,
                sidebar: "tutorialSidebar"
              },
              {
                path: '/docs/concepts/overview',
                component: ComponentCreator('/docs/concepts/overview', 'fee'),
                exact: true,
                sidebar: "tutorialSidebar"
              },
              {
                path: '/docs/concepts/patterns',
                component: ComponentCreator('/docs/concepts/patterns', '22c'),
                exact: true,
                sidebar: "tutorialSidebar"
              },
              {
                path: '/docs/concepts/tools',
                component: ComponentCreator('/docs/concepts/tools', 'd88'),
                exact: true,
                sidebar: "tutorialSidebar"
              },
              {
                path: '/docs/enterprise/configuration',
                component: ComponentCreator('/docs/enterprise/configuration', 'b0d'),
                exact: true,
                sidebar: "tutorialSidebar"
              },
              {
                path: '/docs/enterprise/metrics',
                component: ComponentCreator('/docs/enterprise/metrics', 'bfd'),
                exact: true,
                sidebar: "tutorialSidebar"
              },
              {
                path: '/docs/enterprise/overview',
                component: ComponentCreator('/docs/enterprise/overview', '7c3'),
                exact: true,
                sidebar: "tutorialSidebar"
              },
              {
                path: '/docs/enterprise/security/audit',
                component: ComponentCreator('/docs/enterprise/security/audit', '0f3'),
                exact: true,
                sidebar: "tutorialSidebar"
              },
              {
                path: '/docs/enterprise/security/authentication',
                component: ComponentCreator('/docs/enterprise/security/authentication', '92b'),
                exact: true,
                sidebar: "tutorialSidebar"
              },
              {
                path: '/docs/enterprise/security/authorization',
                component: ComponentCreator('/docs/enterprise/security/authorization', '922'),
                exact: true,
                sidebar: "tutorialSidebar"
              },
              {
                path: '/docs/enterprise/security/overview',
                component: ComponentCreator('/docs/enterprise/security/overview', '8f0'),
                exact: true,
                sidebar: "tutorialSidebar"
              },
              {
                path: '/docs/enterprise/security/sessions',
                component: ComponentCreator('/docs/enterprise/security/sessions', 'a35'),
                exact: true,
                sidebar: "tutorialSidebar"
              },
              {
                path: '/docs/first-agent',
                component: ComponentCreator('/docs/first-agent', '8bc'),
                exact: true,
                sidebar: "tutorialSidebar"
              },
              {
                path: '/docs/installation',
                component: ComponentCreator('/docs/installation', '001'),
                exact: true,
                sidebar: "tutorialSidebar"
              },
              {
                path: '/docs/intro',
                component: ComponentCreator('/docs/intro', 'aed'),
                exact: true,
                sidebar: "tutorialSidebar"
              },
              {
                path: '/docs/quickstart',
                component: ComponentCreator('/docs/quickstart', 'e30'),
                exact: true,
                sidebar: "tutorialSidebar"
              }
            ]
          }
        ]
      }
    ]
  },
  {
    path: '/',
    component: ComponentCreator('/', '5c3'),
    exact: true
  },
  {
    path: '*',
    component: ComponentCreator('*'),
  },
];
