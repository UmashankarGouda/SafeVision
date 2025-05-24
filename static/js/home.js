window.addEventListener("load", function () {
  // Show Hero Section
  const hero = document.getElementById("hero");
  hero.style.opacity = "1";

  // Function to apply animation to multiple elements
  function applyAnimation(selector, animation) {
    document.querySelectorAll(selector).forEach((element) => {
      element.style.animation = animation;
    });
  }
  // Fade in nav and footer separately after preloader is removed
  document.querySelector("nav").style.opacity = "1";
  // Apply animations correctly
  applyAnimation(".hero-content", "showContent 1s 0s ease-in-out forwards");
  applyAnimation(
    "#hero-content-h1",
    "showContent 1s 0.4s ease-in-out forwards"
  );
  applyAnimation(
    "#home-h1-strikes",
    "showContent 1.2s 0.7s ease-in-out forwards"
  );
});
