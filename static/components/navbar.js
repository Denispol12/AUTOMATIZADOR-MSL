(function () {
  'use strict';

  const LINKS = [
    { key: 'pdf',        label: 'Validador PDF',       href: '/'                },
    { key: 'bibtex',     label: 'Validador BibTeX',    href: '/bibtex.html'     },
    { key: 'duplicados', label: 'Eliminar duplicados', href: '/duplicados.html' },
    { key: 'extraccion', label: 'Extracción de datos', href: '/extraccion.html' },
  ];

  const CSS = `
    #navbar-container {
      width: 100%;
      display: block;
    }
    #site-navbar {
      width: 100%;
      background: #0f1117;
      border-bottom: 1px solid #2a2d3e;
      position: sticky;
      top: 0;
      z-index: 1000;
    }
    #site-navbar .nav-inner {
      max-width: 1200px;
      margin: 0 auto;
      display: flex;
      align-items: center;
      padding: 0 1.5rem;
      height: 52px;
    }
    #site-navbar .nav-brand {
      font-family: 'Inter', system-ui, -apple-system, sans-serif;
      font-size: 1rem;
      font-weight: 700;
      color: #FFFFFF;
      letter-spacing: -0.01em;
      white-space: nowrap;
      margin-right: 2rem;
      flex-shrink: 0;
    }
    #site-navbar .nav-links {
      display: flex;
      align-items: center;
      flex: 1;
      height: 100%;
      gap: 0;
    }
    #site-navbar a.nav-link {
      display: inline-flex;
      align-items: center;
      height: 100%;
      padding: 0 1rem;
      font-family: 'Inter', system-ui, -apple-system, sans-serif;
      font-size: 0.85rem;
      font-weight: 500;
      color: #7b7f96;
      text-decoration: none;
      border-bottom: 2px solid transparent;
      transition: color 0.15s, border-color 0.15s, background 0.15s;
      white-space: nowrap;
      box-sizing: border-box;
    }
    #site-navbar a.nav-link:hover {
      color: #e4e6f0;
      background: rgba(255,255,255,0.02);
    }
    #site-navbar a.nav-link.nav-activo {
      color: #e4e6f0;
      font-weight: 600;
      border-bottom-color: #7c6af7;
      background: rgba(124, 106, 247, 0.08);
    }
    #site-navbar .nav-actions {
      display: flex;
      align-items: center;
      gap: 0.5rem;
      margin-left: auto;
    }
    #site-navbar .nav-icon-btn {
      display: flex;
      align-items: center;
      justify-content: center;
      width: 36px;
      height: 36px;
      border-radius: 50%;
      border: none;
      background: transparent;
      color: #7b7f96;
      cursor: pointer;
      transition: color 0.15s, background 0.15s;
    }
    #site-navbar .nav-icon-btn:hover {
      color: #e4e6f0;
      background: rgba(255,255,255,0.05);
    }
    #site-navbar .nav-icon-btn svg {
      width: 20px;
      height: 20px;
      stroke: currentColor;
      fill: none;
      stroke-width: 1.8;
      stroke-linecap: round;
      stroke-linejoin: round;
    }
  `;

  const ICON_USER = `<svg viewBox="0 0 24 24"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>`;
  const ICON_SETTINGS = `<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>`;

  function renderNavbar(paginaActiva) {
    if (!document.getElementById('navbar-styles')) {
      const style = document.createElement('style');
      style.id = 'navbar-styles';
      style.textContent = CSS;
      document.head.appendChild(style);
    }

    const linksHTML = LINKS.map(l => {
      const isActive = l.key === paginaActiva;
      return `<a href="${l.href}" class="nav-link${isActive ? ' nav-activo' : ''}" ${isActive ? 'aria-current="page"' : ''}>${l.label}</a>`;
    }).join('');

    const html = `
      <nav id="site-navbar" role="navigation" aria-label="Navegación principal">
        <div class="nav-inner">
          <span class="nav-brand">MSL Validator</span>
          <div class="nav-links">
            ${linksHTML}
          </div>
          <div class="nav-actions">
            <button class="nav-icon-btn" aria-label="Usuario" title="Perfil de usuario">${ICON_USER}</button>
            <button class="nav-icon-btn" aria-label="Configuración" title="Configuración">${ICON_SETTINGS}</button>
          </div>
        </div>
      </nav>
    `;

    const container = document.getElementById('navbar-container');
    if (container) {
      container.innerHTML = html;
    }
  }

  function autoRender() {
    const pagina = document.body.dataset.page || 'pdf';
    renderNavbar(pagina);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', autoRender);
  } else {
    autoRender();
  }

  window.renderNavbar = renderNavbar;
})();
