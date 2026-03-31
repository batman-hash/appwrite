// Shared auth behavior for all static pages.
// Keeps login/register working even when individual pages have extra scripts.
(function () {
  const AUTH_API_BASE = `${window.location.origin}/api`;
  const PROTECTED_REDIRECT_PATH = "/index.html";

  let currentUser = null;

  function qs(id) {
    return document.getElementById(id);
  }

  function setStatusFromUrl() {
    const statusMessage = qs("statusMessage");
    if (!statusMessage) return;

    const params = new URLSearchParams(window.location.search);
    const hasAuthenticatedUser = !!currentUser || !!localStorage.getItem("user");
    const login = params.get("login");
    const register = params.get("register");
    const activate = params.get("activate");
    const subscribe = params.get("subscribe");
    const reset = params.get("reset");
    const user = params.get("user");

    statusMessage.style.color = "";

    if (user) {
      statusMessage.textContent = "You successfully send your credentials. Access granted.";
      return;
    }
    if (login === "failed") {
      statusMessage.textContent = "Login failed. Please try again.";
      statusMessage.style.color = "#f0f";
      return;
    }
    if (login === "inactive") {
      statusMessage.textContent = "Account not activated. Check your email.";
      statusMessage.style.color = "#f0f";
      return;
    }
    if (login === "locked") {
      statusMessage.textContent = "Too many failed attempts. This email is locked for 24 hours.";
      statusMessage.style.color = "#f0f";
      return;
    }
    if (login === "required") {
      if (hasAuthenticatedUser) {
        statusMessage.textContent = "";
        return;
      }
      statusMessage.textContent = "Login required before you can access the platform.";
      statusMessage.style.color = "#f0f";
      return;
    }
    if (register === "ok") {
      statusMessage.textContent = "Registration successful. Check your email to activate.";
      return;
    }
    if (register === "needed") {
      if (hasAuthenticatedUser) {
        statusMessage.textContent = "";
        return;
      }
      statusMessage.textContent = "Registration required before you can access this page.";
      statusMessage.style.color = "#f0f";
      return;
    }
    if (register === "exists") {
      statusMessage.textContent = "Email already exists.";
      statusMessage.style.color = "#f0f";
      return;
    }
    if (activate === "ok") {
      statusMessage.textContent = "Account activated. You can login now.";
      return;
    }
    if (activate === "invalid") {
      statusMessage.textContent = "Activation link is invalid or expired.";
      statusMessage.style.color = "#f0f";
      return;
    }
    if (subscribe === "ok") {
      statusMessage.textContent = "You successfully send your tags.";
      return;
    }
    if (subscribe === "pending") {
      statusMessage.textContent = "Credentials sent successfully. Check your email to confirm subscription.";
      return;
    }
    if (subscribe === "confirmed") {
      statusMessage.textContent = "Subscription confirmed. Welcome to the newsletter.";
      return;
    }
    if (subscribe === "already") {
      statusMessage.textContent = "Subscription already confirmed for this email.";
      return;
    }
    if (subscribe === "invalid") {
      statusMessage.textContent = "Invalid or expired confirmation link.";
      statusMessage.style.color = "#f0f";
      return;
    }
    if (reset === "sent") {
      statusMessage.textContent = "Password reset email sent.";
      return;
    }
  }

  function setUser(user) {
    if (!user) return;
    const normalized = {
      username: user.username || user.email || "USER",
      email: user.email || "",
      role: user.role || "user",
    };
    currentUser = normalized;
    localStorage.setItem("user", JSON.stringify(normalized));

    const authLinks = qs("authLinks");
    const userLinks = qs("userLinks");
    const usernameLabel = qs("usernameLabel");
    const openLogin = qs("openLogin");
    const openRegister = qs("openRegister");
    const logoutBtn = qs("logoutBtn");

    if (authLinks) authLinks.classList.add("hidden");
    if (userLinks) userLinks.classList.remove("hidden");
    if (openLogin) openLogin.classList.add("hidden");
    if (openRegister) openRegister.classList.add("hidden");
    if (logoutBtn) logoutBtn.classList.remove("hidden");
    if (usernameLabel) usernameLabel.textContent = normalized.username.toUpperCase();
  }

  function clearUser() {
    currentUser = null;
    localStorage.removeItem("user");

    const authLinks = qs("authLinks");
    const userLinks = qs("userLinks");
    const usernameLabel = qs("usernameLabel");
    const openLogin = qs("openLogin");
    const openRegister = qs("openRegister");
    const logoutBtn = qs("logoutBtn");

    if (authLinks) authLinks.classList.remove("hidden");
    if (userLinks) userLinks.classList.add("hidden");
    if (openLogin) openLogin.classList.remove("hidden");
    if (openRegister) openRegister.classList.remove("hidden");
    if (logoutBtn && !userLinks) logoutBtn.classList.add("hidden");
    if (usernameLabel) usernameLabel.textContent = "";
  }

  function restoreUser() {
    const stored = localStorage.getItem("user");
    if (!stored) return;

    try {
      setUser(JSON.parse(stored));
    } catch (_err) {
      clearUser();
    }
  }

  function consumeUrlUser() {
    const params = new URLSearchParams(window.location.search);
    const urlUser = params.get("user");
    if (!urlUser) return;

    setUser({ username: urlUser, email: "", role: "user" });
    params.delete("user");
    const query = params.toString();
    const newUrl = `${window.location.pathname}${query ? "?" + query : ""}`;
    window.history.replaceState({}, document.title, newUrl);
  }

  function showOnly(target, forms) {
    forms.forEach(function (form) {
      if (!form) return;
      form.classList.toggle("hidden", form !== target);
    });
  }

  function initModalUi() {
    const overlay = qs("authOverlay");
    const loginForm = qs("loginForm");
    const registerForm = qs("registerForm");
    const forgotForm = qs("forgotForm");

    const forms = [loginForm, registerForm, forgotForm];

    const openLogin = qs("openLogin");
    const openRegister = qs("openRegister");
    const toRegister = qs("toRegister");
    const toLogin = qs("toLogin");
    const toForgot = qs("toForgot");
    const backToLogin = qs("backToLogin");
    const closeBtn = qs("authClose") || qs("closeOverlay");
    const logoutBtn = qs("logoutBtn");

    function openOverlay(targetForm) {
      if (!overlay) return;
      window.scrollTo({ top: 0, behavior: "smooth" });
      overlay.classList.add("active");
      if (targetForm) showOnly(targetForm, forms);
    }

    function closeOverlay() {
      if (!overlay) return;
      overlay.classList.remove("active");
    }

    // Default state: keep forms separated, show login only.
    if (loginForm) {
      showOnly(loginForm, forms);
    }

    if (openLogin && overlay && loginForm) {
      openLogin.addEventListener("click", function () {
        openOverlay(loginForm);
      });
    }
    if (openRegister && overlay && registerForm) {
      openRegister.addEventListener("click", function () {
        openOverlay(registerForm);
      });
    }
    if (toRegister && registerForm) {
      toRegister.addEventListener("click", function () {
        if (overlay) openOverlay(registerForm);
        else showOnly(registerForm, forms);
      });
    }
    if (toLogin && loginForm) {
      toLogin.addEventListener("click", function () {
        if (overlay) openOverlay(loginForm);
        else showOnly(loginForm, forms);
      });
    }
    if (toForgot && forgotForm) {
      toForgot.addEventListener("click", function () {
        if (overlay) openOverlay(forgotForm);
        else showOnly(forgotForm, forms);
      });
    }
    if (backToLogin && loginForm) {
      backToLogin.addEventListener("click", function () {
        if (overlay) openOverlay(loginForm);
        else showOnly(loginForm, forms);
      });
    }
    if (closeBtn) {
      closeBtn.addEventListener("click", closeOverlay);
    }
    if (overlay) {
      overlay.addEventListener("click", function (e) {
        if (e.target === overlay) closeOverlay();
      });
    }
    if (logoutBtn) {
      logoutBtn.addEventListener("click", async function () {
        try {
          await fetch("/logout", { method: "GET", credentials: "include" });
        } catch (_err) {
          // Always clear local auth state even if server is unreachable.
        }
        clearUser();
        closeOverlay();
      });
    }
  }

  async function submitJson(url, payload) {
    const response = await fetch(url, {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    return response.json();
  }

  async function syncUserFromSession() {
    try {
      const response = await fetch(`${AUTH_API_BASE}/me`, {
        method: "GET",
        credentials: "include",
      });
      if (!response.ok) return false;
      const data = await response.json();
      if (data && data.success && data.user) {
        setUser(data.user);
        return true;
      }
    } catch (_err) {
      // Keep local UI state; network issues should not force logout.
    }
    return false;
  }

  function redirectToProtectedEntry(reason) {
    const target = new URL(`${window.location.origin}${PROTECTED_REDIRECT_PATH}`);
    if (reason === "register") {
      target.searchParams.set("register", "needed");
    } else {
      target.searchParams.set("login", "required");
    }
    window.location.replace(target.toString());
  }

  async function enforceProtectedPage() {
    const body = document.body;
    if (!body || body.dataset.requireAuth !== "true") return;

    const hasStoredUser = !!localStorage.getItem("user");
    const hasSessionUser = await syncUserFromSession();
    if (hasSessionUser) return;

    clearUser();
    redirectToProtectedEntry(hasStoredUser ? "login" : "register");
  }

  function initAjaxLogin() {
    const loginForm = qs("loginForm");
    if (!loginForm || loginForm.hasAttribute("data-standard")) return;

    loginForm.addEventListener("submit", async function (e) {
      e.preventDefault();
      const email = loginForm.email ? loginForm.email.value : "";
      const password = loginForm.password ? loginForm.password.value : "";

      try {
        const data = await submitJson(`${AUTH_API_BASE}/login`, { email, password });
        if (!data.success) throw new Error(data.error || "Login failed");
        setUser(data.user || { username: email, email: email, role: "user" });
        const overlay = qs("authOverlay");
        if (overlay) overlay.classList.remove("active");
      } catch (_err) {
        alert("Login failed. Please check your credentials.");
      }
    });
  }

  function initAjaxRegister() {
    const registerForm = qs("registerForm");
    if (!registerForm || registerForm.hasAttribute("data-standard")) return;

    registerForm.addEventListener("submit", async function (e) {
      e.preventDefault();
      const username = registerForm.username ? registerForm.username.value : "";
      const email = registerForm.email ? registerForm.email.value : "";
      const password = registerForm.password ? registerForm.password.value : "";

      try {
        const data = await submitJson(`${AUTH_API_BASE}/register`, { username, email, password });
        if (!data.success) throw new Error(data.error || "Register failed");
        clearUser();
        const overlay = qs("authOverlay");
        if (overlay) overlay.classList.remove("active");
        alert("Registration saved. Check your email, confirm the newsletter, and wait for approval before login.");
      } catch (_err) {
        alert("Registration failed. Try a different email.");
      }
    });
  }

  function ensureStandardFormTargets() {
    const forms = [
      { id: "loginForm", path: "/login" },
      { id: "registerForm", path: "/register" },
      { id: "forgotForm", path: "/request-reset" },
    ];

    forms.forEach(function (entry) {
      const form = qs(entry.id);
      if (!form || !form.hasAttribute("data-standard")) return;

      const base = window.location.origin;
      if (base && base.startsWith("http")) {
        form.action = `${base}${entry.path}`;
      }

      let nextInput = form.querySelector('input[name="next"]');
      if (!nextInput) {
        nextInput = document.createElement("input");
        nextInput.type = "hidden";
        nextInput.name = "next";
        form.appendChild(nextInput);
      }
      nextInput.value = `${window.location.origin}${window.location.pathname}`;
    });
  }

  function initAjaxForgot() {
    const forgotForm = qs("forgotForm");
    if (!forgotForm || forgotForm.hasAttribute("data-standard")) return;

    forgotForm.addEventListener("submit", async function (e) {
      e.preventDefault();
      const email = forgotForm.email ? forgotForm.email.value : "";
      if (!email) {
        alert("Please enter your email.");
        return;
      }
      try {
        const data = await submitJson(`${AUTH_API_BASE}/request-reset`, { email: email });
        if (!data.success) throw new Error(data.error || "Reset request failed");
        const overlay = qs("authOverlay");
        if (overlay) overlay.classList.remove("active");
        alert("Password reset email sent.");
      } catch (_err) {
        alert("Reset request failed. Please try again.");
      }
    });
  }

  async function init() {
    restoreUser();
    await enforceProtectedPage();
    await syncUserFromSession();
    consumeUrlUser();
    ensureStandardFormTargets();
    initModalUi();
    initAjaxLogin();
    initAjaxRegister();
    initAjaxForgot();
    setStatusFromUrl();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }

  window.AuthState = {
    setUser: setUser,
    clearUser: clearUser,
    getUser: function () {
      return currentUser;
    },
  };
})();


