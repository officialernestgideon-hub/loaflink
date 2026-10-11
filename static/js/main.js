document.addEventListener('DOMContentLoaded', () => {

  /* ============ NAV SCROLL EFFECT ============ */
  const nav = document.getElementById('nav');
  const onScroll = () => {
    if (window.scrollY > 20) {
      nav.classList.add('scrolled');
    } else {
      nav.classList.remove('scrolled');
    }
  };
  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();

  /* ============ MOBILE MENU TOGGLE ============ */
  const menuToggle = document.getElementById('menuToggle');
  const menuIcon   = document.getElementById('menuToggleIcon');
  const navLinks   = document.getElementById('navLinks');
  const backdrop   = document.getElementById('navBackdrop');

  const openMenu = () => {
    navLinks.classList.add('open');
    menuToggle.classList.add('active');
    menuToggle.setAttribute('aria-expanded', 'true');
    backdrop.classList.add('active');
    document.body.classList.add('menu-open');
    if (menuIcon) {
      menuIcon.classList.remove('fa-bars');
      menuIcon.classList.add('fa-xmark');
    }
  };

  const closeMenu = () => {
    navLinks.classList.remove('open');
    menuToggle.classList.remove('active');
    menuToggle.setAttribute('aria-expanded', 'false');
    backdrop.classList.remove('active');
    document.body.classList.remove('menu-open');
    if (menuIcon) {
      menuIcon.classList.remove('fa-xmark');
      menuIcon.classList.add('fa-bars');
    }
  };

  const toggleMenu = () => {
    if (navLinks.classList.contains('open')) {
      closeMenu();
    } else {
      openMenu();
    }
  };

  if (menuToggle && navLinks) {
    menuToggle.addEventListener('click', toggleMenu);
  }

  /* Close when backdrop clicked */
  if (backdrop) {
    backdrop.addEventListener('click', closeMenu);
  }

  /* Close when a link inside the dropdown is clicked */
  if (navLinks) {
    navLinks.querySelectorAll('a').forEach(link => {
      link.addEventListener('click', () => {
        if (window.innerWidth <= 900) closeMenu();
      });
    });
  }

  /* Close when resizing to desktop */
  let resizeTimer;
  window.addEventListener('resize', () => {
    clearTimeout(resizeTimer);
    resizeTimer = setTimeout(() => {
      if (window.innerWidth > 900) closeMenu();
    }, 150);
  });

  /* ESC key closes menu */
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') closeMenu();
  });

  /* ============ REVEAL ON SCROLL ============ */
  const reveals = document.querySelectorAll('.reveal');
  if ('IntersectionObserver' in window && reveals.length) {
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('visible');
          observer.unobserve(entry.target);
        }
      });
    }, {
      threshold: 0.12,
      rootMargin: '0px 0px -60px 0px'
    });

    reveals.forEach(el => observer.observe(el));
  } else {
    // Fallback: just show them all
    reveals.forEach(el => el.classList.add('visible'));
  }

});
