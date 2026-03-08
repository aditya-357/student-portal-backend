let isStudent = true;

const studentBtn = document.getElementById("studentBtn");
const adminBtn = document.getElementById("adminBtn");
const loginBtn = document.getElementById("loginBtn");
const message = document.getElementById("message");

studentBtn.addEventListener("click", () => {
    isStudent = true;
    studentBtn.classList.add("active");
    adminBtn.classList.remove("active");
});

adminBtn.addEventListener("click", () => {
    isStudent = false;
    adminBtn.classList.add("active");
    studentBtn.classList.remove("active");
});

loginBtn.addEventListener("click", async () => {
    const username = document.getElementById("username").value;
    const password = document.getElementById("password").value;

    let endpoint = isStudent ? "/student/login" : "/admin/login";

    let payload = isStudent ?
        { student_id: username, password: password } :
        { admin_id: username, password: password };

    const response = await fetch(endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
    });

    const data = await response.json();

    if (response.ok) {
        message.style.color = "lightgreen";
        message.innerText = "Login successful!";
        window.location.href = isStudent ? "/student/dashboard" : "/admin/dashboard";
    } else {
        message.style.color = "yellow";
        message.innerText = data.message;
    }
});
