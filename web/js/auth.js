function setError(inputId, errorId, message) {
  const input = document.getElementById(inputId);
  const errorText = document.getElementById(errorId);

  if (input) {
    input.classList.toggle("input-error", !!message);
  }

  if (errorText) {
    errorText.textContent = message || "";
  }
}

function clearError(inputId, errorId) {
  setError(inputId, errorId, "");
}

function setLoading(buttonId, isLoading) {
  const button = document.getElementById(buttonId);
  if (!button) return;

  const text = button.querySelector(".btn-text");
  const loader = button.querySelector(".btn-loader");

  button.disabled = isLoading;

  if (text) text.classList.toggle("hidden", isLoading);
  if (loader) loader.classList.toggle("hidden", !isLoading);
}

document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll(".toggle-password").forEach((button) => {
    button.addEventListener("click", () => {
      const targetId = button.dataset.target;
      const input = document.getElementById(targetId);
      if (!input) return;

      const isPassword = input.type === "password";
      input.type = isPassword ? "text" : "password";
      button.textContent = isPassword ? "Hide" : "Show";
    });
  });

  const adminForm = document.getElementById("adminLoginForm");
  if (adminForm) {
    const emailInput = document.getElementById("admin-email");
    const passwordInput = document.getElementById("admin-password");

    emailInput.addEventListener("input", () => clearError("admin-email", "admin-email-error"));
    passwordInput.addEventListener("input", () => clearError("admin-password", "admin-password-error"));

    adminForm.addEventListener("submit", async (e) => {
      e.preventDefault();

      const email = emailInput.value.trim();
      const password = passwordInput.value.trim();

      let hasError = false;

      if (!email) {
        setError("admin-email", "admin-email-error", "Email is required");
        hasError = true;
      }

      if (!password) {
        setError("admin-password", "admin-password-error", "Password is required");
        hasError = true;
      }

      if (hasError) return;

      if (email === "admin@gmail.com" && password === "admin123") {
        alert("Default Admin Login Successful");
        localStorage.setItem("role", "admin");
        localStorage.setItem("admin_id", "1");
        localStorage.setItem("admin_name", "Super Admin");
        localStorage.setItem("admin_email", "admin@gmail.com");
        localStorage.setItem("admin_phone", "+91 98765 43210");
        window.location.href = "dashboard.html";
        return;
      }

      try {
        setLoading("admin-login-btn", true);

        const result = await apiRequest("/admin/login", "POST", { email, password });

        localStorage.setItem("token", result.access_token || "");
        localStorage.setItem("role", "admin");
        localStorage.setItem("admin_id", result.admin_id || "");
        localStorage.setItem("admin_name", result.name || "Admin");
        localStorage.setItem("admin_email", email);
        localStorage.setItem("admin_phone", result.phone || "");

        alert(result.message || "Admin Login Successful");
        window.location.href = "dashboard.html";
      } catch (error) {
        alert(`Login Failed: ${error.message}`);
      } finally {
        setLoading("admin-login-btn", false);
      }
    });
  }

  const dealerForm = document.getElementById("dealerLoginForm");
  if (dealerForm) {
    const emailInput = document.getElementById("dealer-email");
    const passwordInput = document.getElementById("dealer-password");

    emailInput.addEventListener("input", () => clearError("dealer-email", "dealer-email-error"));
    passwordInput.addEventListener("input", () => clearError("dealer-password", "dealer-password-error"));

    dealerForm.addEventListener("submit", async (e) => {
      e.preventDefault();

      const email = emailInput.value.trim();
      const password = passwordInput.value.trim();

      let hasError = false;

      if (!email) {
        setError("dealer-email", "dealer-email-error", "Email is required");
        hasError = true;
      }

      if (!password) {
        setError("dealer-password", "dealer-password-error", "Password is required");
        hasError = true;
      }

      if (hasError) return;

      try {
        setLoading("dealer-login-btn", true);

        const result = await apiRequest("/dealer/login", "POST", { email, password });

        localStorage.setItem("token", result.access_token || "");
        localStorage.setItem("role", "dealer");
        localStorage.setItem("dealer_id", result.dealer_id || "");
        localStorage.setItem("dealer_name", result.name || "Dealer");
        localStorage.setItem("dealer_email", email);
        localStorage.setItem("dealer_phone", result.phone || "");

        alert(result.message || "Dealer Login Successful");
        window.location.href = "dashboard.html";
      } catch (error) {
        alert(`Login Failed: ${error.message}`);
      } finally {
        setLoading("dealer-login-btn", false);
      }
    });
  }

  const userForm = document.getElementById("userLoginForm");
  if (userForm) {
    const emailInput = document.getElementById("user-email");
    const passwordInput = document.getElementById("user-password");

    emailInput.addEventListener("input", () => clearError("user-email", "user-email-error"));
    passwordInput.addEventListener("input", () => clearError("user-password", "user-password-error"));

    userForm.addEventListener("submit", async (e) => {
      e.preventDefault();

      const email = emailInput.value.trim();
      const password = passwordInput.value.trim();

      let hasError = false;

      if (!email) {
        setError("user-email", "user-email-error", "Email is required");
        hasError = true;
      }

      if (!password) {
        setError("user-password", "user-password-error", "Password is required");
        hasError = true;
      }

      if (hasError) return;

      try {
        setLoading("user-login-btn", true);

        const result = await apiRequest("/user/login", "POST", { email, password });

        localStorage.setItem("token", result.access_token || "");
        localStorage.setItem("role", "user");
        localStorage.setItem("user_id", result.user_id || "1");
        localStorage.setItem("user_name", result.name || "User");
        localStorage.setItem("user_email", email);
        localStorage.setItem("user_phone", result.phone || "");
        localStorage.setItem("pds_verified", String(!!result.pds_verified));
        localStorage.setItem("pds_card_no", result.pds_card_no || "");

        alert(result.message || "Login Successful");
        window.location.href = "dashboard.html";
      } catch (error) {
        alert(`Error: ${error.message}`);
      } finally {
        setLoading("user-login-btn", false);
      }
    });
  }
});