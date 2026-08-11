/* Card Dealer Pro 2.0 — Application Script */

(function () {
  'use strict';

  /* ===== Mobile Navigation Toggle ===== */
  const navToggle = document.querySelector('.nav-toggle');
  const navLinks = document.querySelector('.nav-links');
  const navActions = document.querySelector('.nav-actions');

  if (navToggle) {
    navToggle.addEventListener('click', function () {
      const isOpen = navLinks && navLinks.classList.contains('mobile-open');

      if (navLinks) {
        navLinks.classList.toggle('mobile-open', !isOpen);
      }
      if (navActions) {
        navActions.classList.toggle('mobile-open', !isOpen);
        if (!isOpen && navLinks) {
          // Position actions dropdown below the expanded nav links
          const navLinksBottom = navLinks.getBoundingClientRect().bottom;
          navActions.style.top = navLinksBottom + 'px';
        }
      }
    });
  }

  /* ===== Smooth active state for nav links ===== */
  const sections = document.querySelectorAll('section[id]');
  const navAnchors = document.querySelectorAll('.nav-links a');

  function updateActiveNavLink() {
    const scrollY = window.scrollY + 80;

    sections.forEach(function (section) {
      const top = section.offsetTop;
      const height = section.offsetHeight;
      const id = section.getAttribute('id');

      if (scrollY >= top && scrollY < top + height) {
        navAnchors.forEach(function (a) {
          a.classList.toggle('active', a.getAttribute('href') === '#' + id);
        });
      }
    });
  }

  window.addEventListener('scroll', updateActiveNavLink, { passive: true });
  updateActiveNavLink();

  /* ===== Inventory filter tabs ===== */
  const filterTags = document.querySelectorAll('.filter-tag');

  filterTags.forEach(function (tag) {
    tag.addEventListener('click', function () {
      const parent = tag.closest('.inv-filters');
      if (parent) {
        parent.querySelectorAll('.filter-tag').forEach(function (t) {
          t.classList.remove('active');
        });
      }
      tag.classList.add('active');
    });
  });

  /* ===== Sidebar navigation in mockup ===== */
  const sidebarItems = document.querySelectorAll('.sidebar-item');

  sidebarItems.forEach(function (item) {
    item.addEventListener('click', function () {
      sidebarItems.forEach(function (i) {
        i.classList.remove('active');
      });
      item.classList.add('active');
    });
  });

  /* ===== Intersection Observer for fade-in animations ===== */
  if ('IntersectionObserver' in window) {
    const animatables = document.querySelectorAll(
      '.feature-card, .marketplace-card, .pricing-card, .mockup-card'
    );

    animatables.forEach(function (el) {
      el.style.opacity = '0';
      el.style.transform = 'translateY(20px)';
      el.style.transition = 'opacity 0.4s ease, transform 0.4s ease';
    });

    const observer = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            entry.target.style.opacity = '1';
            entry.target.style.transform = 'translateY(0)';
            observer.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.1, rootMargin: '0px 0px -40px 0px' }
    );

    animatables.forEach(function (el) {
      observer.observe(el);
    });
  }

  /* ===== CTA button click tracking (placeholder) ===== */
  document.querySelectorAll('.btn').forEach(function (btn) {
    btn.addEventListener('click', function (e) {
      const href = btn.getAttribute('href');
      if (href === '#') {
        e.preventDefault();
      }
    });
  });
}());
