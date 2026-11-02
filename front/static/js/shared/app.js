(() => {
  const sidebar = document.getElementById('sidebar');
  const toggle = document.getElementById('menuToggle');
  const mobileLayout = window.matchMedia('(max-width: 900px)');

  if (sidebar && toggle) {
    const savedCollapsed = () => localStorage.getItem('assetverify-sidebar-collapsed') === 'true';
    document.body.classList.toggle('sidebar-collapsed', !mobileLayout.matches && savedCollapsed());

    const setExpanded = expanded => {
      sidebar.classList.toggle('open', expanded);
      toggle.setAttribute('aria-expanded', String(expanded));
      toggle.setAttribute('aria-label', expanded ? 'Close navigation' : 'Open navigation');
    };

    toggle.addEventListener('click', () => {
      if (mobileLayout.matches) {
        setExpanded(!sidebar.classList.contains('open'));
      } else {
        const collapsed = document.body.classList.toggle('sidebar-collapsed');
        localStorage.setItem('assetverify-sidebar-collapsed', String(collapsed));
      }
    });

    mobileLayout.addEventListener('change', event => {
      setExpanded(false);
      document.body.classList.toggle('sidebar-collapsed', !event.matches && savedCollapsed());
    });

    document.addEventListener('click', event => {
      if (mobileLayout.matches && sidebar.classList.contains('open') &&
          !sidebar.contains(event.target) && !toggle.contains(event.target)) setExpanded(false);
    });
    sidebar.querySelectorAll('a.nav-link').forEach(link => link.addEventListener('click', () => setExpanded(false)));
  }

  const backButton = document.getElementById('backButton');
  if (backButton) backButton.addEventListener('click', () => {
    try {
      if (document.referrer && new URL(document.referrer).origin === window.location.origin) {
        window.history.back();
        return;
      }
    } catch (_) { /* Use the dashboard when there is no safe in-app page to return to. */ }
    window.location.assign('/dashboard');
  });

  document.addEventListener('click', event => {
    document.querySelectorAll('.profile-menu[open]').forEach(menu => {
      if (!menu.contains(event.target)) menu.removeAttribute('open');
    });
  });

  document.querySelectorAll('form[data-loading]').forEach(form => form.addEventListener('submit', () => {
    const button = form.querySelector('button[type="submit"],button:not([type])');
    if (button && form.reportValidity()) { button.disabled = true; button.dataset.original = button.innerHTML; button.innerHTML = `<span class="spinner"></span>${form.dataset.loading}`; }
  }));
  document.querySelectorAll('.show-password').forEach(button => button.addEventListener('click', () => {
    const input = button.parentElement.querySelector('input');
    input.type = input.type === 'password' ? 'text' : 'password';
    button.innerHTML = `<i class="bi ${input.type === 'password' ? 'bi-eye' : 'bi-eye-slash'}"></i>`;
  }));
  document.querySelectorAll('.toast').forEach(toast => setTimeout(() => { toast.classList.add('toast-out'); setTimeout(() => toast.remove(), 350); }, 5500));
})();
