// Focus on password field when page loads
document.addEventListener("DOMContentLoaded", function () {
  document.getElementById("password").focus();
});

// Show/hide password toggle (optional enhancement)
function togglePassword() {
  const passwordField = document.getElementById("password");
  const toggleIcon = document.getElementById("toggle-icon");

  if (passwordField.type === "password") {
    passwordField.type = "text";
    toggleIcon.className = "fas fa-eye-slash";
  } else {
    passwordField.type = "password";
    toggleIcon.className = "fas fa-eye";
  }
}
