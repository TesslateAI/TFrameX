// @ts-check
// Note: type annotations allow type checking and IDEs autocompletion

const {themes} = require('prism-react-renderer');
const lightCodeTheme = themes.github;
const darkCodeTheme = themes.dracula;

/** @type {import('@docusaurus/types').Config} */
const config = {
  title: 'TFrameX',
  tagline: 'The Extensible Task & Flow Orchestration Framework for LLMs',
  favicon: 'img/favicon.ico',

  // Set the production url of your site here
  url: 'https://tframex.tesslate.com',
  // Set the /<baseUrl>/ pathname under which your site is served
  baseUrl: '/',

  // GitHub pages deployment config.
  organizationName: 'TesslateAI',
  projectName: 'TFrameX',

  onBrokenLinks: 'throw',
  onBrokenMarkdownLinks: 'warn',

  // Even if you don't use internalization, you can use this field to set useful
  // metadata like html lang. For example, if your site is Chinese, you may want
  // to replace "en" with "zh-Hans".
  i18n: {
    defaultLocale: 'en',
    locales: ['en'],
  },

  presets: [
    [
      'classic',
      /** @type {import('@docusaurus/preset-classic').Options} */
      ({
        docs: {
          sidebarPath: require.resolve('./sidebars.js'),
          // Please change this to your repo.
          editUrl: 'https://github.com/TesslateAI/TFrameX/tree/main/docs-site/',
        },
        blog: {
          showReadingTime: true,
          // Please change this to your repo.
          editUrl: 'https://github.com/TesslateAI/TFrameX/tree/main/docs-site/',
        },
        theme: {
          customCss: require.resolve('./src/css/custom.css'),
        },
      }),
    ],
  ],

  themeConfig:
    /** @type {import('@docusaurus/preset-classic').ThemeConfig} */
    ({
      // Replace with your project's social card
      image: 'img/tframex-social-card.jpg',
      navbar: {
        title: 'TFrameX',
        logo: {
          alt: 'TFrameX Logo',
          src: 'img/logo.svg',
        },
        items: [
          {
            type: 'docSidebar',
            sidebarId: 'tutorialSidebar',
            position: 'left',
            label: 'Documentation',
          },
          {
            to: '/docs/api/overview',
            label: 'API',
            position: 'left',
          },
          {
            to: '/docs/cli/overview',
            label: 'CLI',
            position: 'left',
          },
          {
            to: '/docs/enterprise/overview',
            label: 'Enterprise',
            position: 'left',
          },
          {to: '/blog', label: 'Blog', position: 'left'},
          {
            href: 'https://github.com/TesslateAI/TFrameX',
            label: 'GitHub',
            position: 'right',
          },
        ],
      },
      footer: {
        style: 'dark',
        links: [
          {
            title: 'Docs',
            items: [
              {
                label: 'Getting Started',
                to: '/docs/intro',
              },
              {
                label: 'CLI Reference',
                to: '/docs/cli/overview',
              },
              {
                label: 'API Reference',
                to: '/docs/api/overview',
              },
            ],
          },
          {
            title: 'Community',
            items: [
              {
                label: 'Discord',
                href: 'https://discord.gg/DkzMzwBTaw',
              },
              {
                label: 'GitHub',
                href: 'https://github.com/TesslateAI/TFrameX',
              },
              {
                label: 'Twitter',
                href: 'https://twitter.com/tesslateai',
              },
            ],
          },
          {
            title: 'More',
            items: [
              {
                label: 'Blog',
                to: '/blog',
              },
              {
                label: 'Tesslate Studio',
                href: 'https://github.com/TesslateAI/Studio',
              },
            ],
          },
        ],
        copyright: `Copyright © ${new Date().getFullYear()} TesslateAI. Built with Docusaurus.`,
      },
      prism: {
        theme: lightCodeTheme,
        darkTheme: darkCodeTheme,
        additionalLanguages: ['python', 'bash', 'json', 'yaml'],
      },
      algolia: {
        // The application ID provided by Algolia
        appId: 'YOUR_APP_ID',
        // Public API key: it is safe to commit it
        apiKey: 'YOUR_SEARCH_API_KEY',
        indexName: 'tframex',
        // Optional: see doc section below
        contextualSearch: true,
      },
    }),
};

module.exports = config;