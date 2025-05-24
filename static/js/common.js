function toggleMobileMenu() {
  const menu = document.getElementById("nav-menu");
  const toggle = document.querySelector(".mobile-menu-toggle i");

  if (menu.classList.contains("active")) {
    menu.classList.remove("active");
    toggle.className = "fas fa-bars";
  } else {
    menu.classList.add("active");
    toggle.className = "fas fa-times";
  }
}

// Close mobile menu when clicking on a link
document.addEventListener("DOMContentLoaded", function () {
  const navLinks = document.querySelectorAll("#nav-menu a");
  const menu = document.getElementById("nav-menu");
  const toggle = document.querySelector(".mobile-menu-toggle i");

  navLinks.forEach((link) => {
    link.addEventListener("click", () => {
      if (menu.classList.contains("active")) {
        menu.classList.remove("active");
        toggle.className = "fas fa-bars";
      }
    });
  });

  // Close menu when clicking outside
  document.addEventListener("click", function (event) {
    const navbar = document.getElementById("navbar");
    if (!navbar.contains(event.target) && menu.classList.contains("active")) {
      menu.classList.remove("active");
      toggle.className = "fas fa-bars";
    }
  });
});
