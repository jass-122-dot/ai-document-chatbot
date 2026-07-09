document
  .getElementById("registerForm")
  .addEventListener("submit", function (e) {
    e.preventDefault();
    const name = document.getElementById("name").value;
    const email = document.getElementById("email").value;
    const password = document.getElementById("password").value;
    const errorMsg = document.getElementById("error-msg");

    fetch("/api/auth/register", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, email, password }),
    })
      .then((r) => r.json())
      .then((data) => {
        if (data.message) {
          fetch("/api/auth/login", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email, password }),
          })
            .then((r) => r.json())
            .then((loginData) => {
              localStorage.setItem("token", loginData.token);
              localStorage.setItem("name", loginData.name);
              localStorage.setItem("user_id", loginData.user_id);
              window.location.replace("/dashboard");
            });
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
