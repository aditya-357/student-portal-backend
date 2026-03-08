const sendOtpBtn = document.getElementById("sendOtpBtn");
const message = document.getElementById("message");

sendOtpBtn.addEventListener("click", async () => {
    const studentId = document.getElementById("student_id").value;

    if (!studentId) {
        message.innerText = "Please enter Student ID";
        return;
    }

    const response = await fetch("/student/forgot-password", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ student_id: studentId })
    });

    const data = await response.json();

    if (response.ok) {
        // Save student + cooldown time
        localStorage.setItem("reset_student", studentId);
        localStorage.setItem("otp_timer", Date.now() + 60000);

        // Redirect immediately
        window.location.href = "/reset-password";
    } else {
        message.innerText = data.message;
    }
});
