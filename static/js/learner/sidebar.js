document.addEventListener('DOMContentLoaded', function() {
    const sidebar = document.getElementById('sidebar');
    const toggleSidebarMobile = document.getElementById('toggleSidebarMobile');
    const mainContent = document.getElementById('main-content');

    function toggleSidebar() {
        sidebar.classList.toggle('sidebar-closed');
        mainContent.classList.toggle('lg:ml-0');
        mainContent.classList.toggle('lg:ml-64');
    }

    toggleSidebarMobile.addEventListener('click', toggleSidebar);
});