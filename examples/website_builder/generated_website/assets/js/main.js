// Navigation: Hamburger Menu Toggle
const hamburger = document.querySelector('.hamburger');
const nav = document.querySelector('nav');

hamburger.addEventListener('click', () => {
  nav.classList.toggle('active');
});

// Scrollspy: Highlight Active Navigation Link
window.addEventListener('scroll', () => {
  const sections = document.querySelectorAll('section');
  const navLinks = document.querySelectorAll('nav a');

  sections.forEach(section => {
    const sectionTop = section.offsetTop;
    const sectionHeight = section.clientHeight;
    const scrollPosition = window.scrollY;

    if (scrollPosition >= sectionTop - 100 && scrollPosition < sectionTop + sectionHeight - 100) {
      navLinks.forEach(link => link.classList.remove('active'));
      const activeLink = document.querySelector(`nav a[href="#${section.id}"]`);
      if (activeLink) activeLink.classList.add('active');
    }
  });
});

// Hero Text Animation on Load
window.addEventListener('load', () => {
  const heroText = document.querySelector('.hero-text');
  if (heroText) heroText.classList.add('animate');
});

// Gallery: Filterable Image Grid
document.querySelectorAll('.filter-btn').forEach(button => {
  button.addEventListener('click', () => {
    const category = button.getAttribute('data-category');
    document.querySelectorAll('.gallery-item').forEach(item => {
      if (category === 'all' || item.getAttribute('data-category') === category) {
        item.style.display = 'block';
      } else {
        item.style.display = 'none';
      }
    });
  });
});

// Gallery: Lightbox Initialization with Fancybox
document.addEventListener('DOMContentLoaded', () => {
  if (typeof Fancybox !== 'undefined') {
    Fancybox.bind("[data-fancybox]", {
      // Fancybox options
    });
  }
});

// Form: Modal Popup Trigger
document.querySelector('.contact-link').addEventListener('click', (e) => {
  e.preventDefault();
  document.getElementById('contact-modal').style.display = 'block';
});

// Form: Close Modal on Close Button Click
document.querySelector('.close-modal').addEventListener('click', () => {
  document.getElementById('contact-modal').style.display = 'none';
});

// Mobile Menu Toggle (Duplicate for Consistency)
document.querySelector('.hamburger').addEventListener('click', () => {
  const nav = document.querySelector('nav');
  nav.classList.toggle('active');
});