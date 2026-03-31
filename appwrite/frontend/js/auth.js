// Shared auth behavior for all static pages.
// Keeps login/register working even when individual pages have extra scripts.
(function () {
  const AUTH_API_BASE = `${window.location.origin}/api`;
  const PROTECTED_REDIRECT_PATH = "/";

  let currentUser = null;

  function qs(id) {
    return document.getElementById(id);
  }

  function setStatusMessage(text, color) {
    const statusMessage = qs("statusMessage");
    if (!statusMessage) return;
    statusMessage.textContent = text || "";
    statusMessage.style.color = color || "";
  }

  function setStatusFromUrl() {
    const params = new URLSearchParams(window.location.search);
    const hasAuthenticatedUser = !!currentUser || !!localStorage.getItem("user");

    if (params.get("user")) {
      setStatusMessage("You successfully send your credentials. Access granted.");
      return;
    }
    if (params.get("login") === "failed") {
      setStatusMessage("Login failed. Please try again.", "#f0f");
      return;
    }
    if (params.get("login") === "inactive") {
      setStatusMessage("Account not activated. Check your email.", "#f0f");
      return;
    }
    if (params.get("login") === "locked") {
      setStatusMessage("Too many failed attempts. This email is locked for 24 hours.", "#f0f");
      return;
    }
    if (params.get("login") === "required") {
      if (!hasAuthenticatedUser) {
        setStatusMessage("Login required before you can access the platform.", "#f0f");
      }
      return;
    }
    if (params.get("register") === "ok") {
      setStatusMessage("Registration successful. Check your email to activate.");
      return;
    }
    if (params.get("register") === "needed") {
      if (!hasAuthenticatedUser) {
        setStatusMessage("Registration required before you can access this page.", "#f0f");
      }
      return;
    }
    if (params.get("register") === "exists") {
      setStatusMessage("Email already exists.", "#f0f");
      return;
    }
    if (params.get("activate") === "ok") {
      setStatusMessage("Account activated. You can login now.");
      return;
    }
    if (params.get("activate") === "invalid") {
      setStatusMessage("Activation link is invalid or expired.", "#f0f");
      return;
    }
    if (params.get("subscribe") === "ok") {
      setStatusMessage("You successfully send your tags.");
      return;
    }
    if (params.get("subscribe") === "pending") {
      setStatusMessage("Credentials sent successfully. Check your email to confirm subscription.");
      return;
    }
    if (params.get("subscribe") === "confirmed") {
      setStatusMessage("Subscription confirmed. Welcome to the newsletter.");
      return;
    }
    if (params.get("subscribe") === "already") {
      setStatusMessage("Subscription already confirmed for this email.");
      return;
    }
    if (params.get("subscribe") === "invalid") {
      setStatusMessage("Invalid or expired confirmation link.", "#f0f");
      return;
    }
    if (params.get("reset") === "sent") {
      setStatusMessage("Password reset email sent.");
    }
  }

  function updateAuthUi(isSignedIn) {
    const authLinks = qs("authLinks");
    const userLinks = qs("userLinks");
    const openLogin = qs("openLogin");
    const openRegister = qs("openRegister");
    const logoutBtn = qs("logoutBtn");
    if (authLinks) authLinks.classList.toggle("hidden", !!isSignedIn);
    if (userLinks) userLinks.classList.toggle("hidden", !isSignedIn);
    if (openLogin) openLogin.classList.toggle("hidden", !!isSignedIn);
    if (openRegister) openRegister.classList.toggle("hidden", !!isSignedIn);
    if (logoutBtn) logoutBtn.classList.toggle("hidden", !isSignedIn && !!userLinks);
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

    const usernameLabel = qs("usernameLabel");
    updateAuthUi(true);
    if (usernameLabel) usernameLabel.textContent = normalized.username.toUpperCase();
  }

  function clearUser() {
    currentUser = null;
    localStorage.removeItem("user");
    const usernameLabel = qs("usernameLabel");
    updateAuthUi(false);
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
    const newUrl = `${window.location.pathname}${query ? `?${query}` : ""}`;
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

    if (loginForm) showOnly(loginForm, forms);
    if (openLogin && overlay && loginForm) openLogin.addEventListener("click", function () { openOverlay(loginForm); });
    if (openRegister && overlay && registerForm) openRegister.addEventListener("click", function () { openOverlay(registerForm); });
    if (toRegister && registerForm) toRegister.addEventListener("click", function () { overlay ? openOverlay(registerForm) : showOnly(registerForm, forms); });
    if (toLogin && loginForm) toLogin.addEventListener("click", function () { overlay ? openOverlay(loginForm) : showOnly(loginForm, forms); });
    if (toForgot && forgotForm) toForgot.addEventListener("click", function () { overlay ? openOverlay(forgotForm) : showOnly(forgotForm, forms); });
    if (backToLogin && loginForm) backToLogin.addEventListener("click", function () { overlay ? openOverlay(loginForm) : showOnly(loginForm, forms); });
    if (closeBtn) closeBtn.addEventListener("click", closeOverlay);
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
