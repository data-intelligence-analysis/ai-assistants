document.addEventListener('DOMContentLoaded', function () {
  const sidebar = document.getElementById('sidebar-wrapper');
  const toggleBtn = document.getElementById('sidebarToggleBtn');
  const backdrop = document.getElementById('sidebarBackdrop');

  if (!sidebar || !toggleBtn || !backdrop) {
    return;
  }

  function openSidebar() {
    sidebar.classList.add('open');
    backdrop.classList.add('active');
    document.body.classList.add('sidebar-open');
  }

  function closeSidebar() {
    sidebar.classList.remove('open');
    backdrop.classList.remove('active');
    document.body.classList.remove('sidebar-open');
  }

  toggleBtn.addEventListener('click', function () {
    if (sidebar.classList.contains('open')) {
      closeSidebar();
    } else {
      openSidebar();
    }
  });

  backdrop.addEventListener('click', closeSidebar);

  window.addEventListener('resize', function () {
    if (window.innerWidth >= 1280) {
      closeSidebar();
    }
  });
});
