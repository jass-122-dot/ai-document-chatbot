document.getElementById("loginForm").addEventListener("submit", function (e) {
  e.preventDefault();
  const email = document.getElementById("email").value;
  const password = document.getElementById("password").value;
  const errorMsg = document.getElementById("error-msg");

  fetch("/api/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  })
    .then((r) => r.json())
    .then((data) => {
      if (data.token) {
        localStorage.setItem("token", data.token);
        localStorage.setItem("name", data.name);
        localStorage.setItem("user_id", data.user_id);
        window.location.replace("/dashboard");
      } else {
        errorMsg.style.display = "block";
        errorMsg.textContent = data.error;
      }
    })
    .catch(() => {
      errorMsg.style.display = "block";
      errorMsg.textContent = "Something went wrong. Try again.";
    });
});
