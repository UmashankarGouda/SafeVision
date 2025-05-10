document.addEventListener("DOMContentLoaded", function () {
  // Add animation to reveal elements as they scroll into view
  const animateElements = document.querySelectorAll(
    ".tech-item, .team-member, .value, .col-left, .col-right"
  );

  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add("animate-in");
          observer.unobserve(entry.target);
        }
      });
    },
    {
      threshold: 0.1,
    }
  );

  animateElements.forEach((element) => {
    observer.observe(element);
  });
});
