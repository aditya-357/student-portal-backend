const resetBtn = document.getElementById("resetBtn");
const resendBtn = document.getElementById("resendBtn");
const message = document.getElementById("message");

function checkCooldown() {
    const savedTime = localStorage.getItem("otp_timer");

    if (savedTime) {
        const timeLeft = Math.floor((savedTime - Date.now()) / 1000);

        if (timeLeft > 0) {
            resendBtn.disabled = true;
            resendBtn.innerText = `Resend OTP (${timeLeft}s)`;

            const interval = setInterval(() => {
                const newTimeLeft = Math.floor((savedTime - Date.now()) / 1000);

                if (newTimeLeft <= 0) {
                    clearInterval(interval);
                    resendBtn.disabled = false;
                    resendBtn.innerText = "Resend OTP";
                    localStorage.removeItem("otp_timer");
                } else {
                    resendBtn.innerText = `Resend OTP (${newTimeLeft}s)`;
                }
            }, 1000);
        }
    }
}

document.addEventListener("DOMContentLoaded", () => {
    const storedStudent = localStorage.getItem("reset_student");
    if (storedStudent) {
        document.getElementById("student_id").value = storedStudent;
    }

    checkCooldown();
});

resendBtn.addEventListener("click", async () => {
    const studentId = document.getElementById("student_id").value;

    const response = await fetch("/student/forgot-password", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ student_id: studentId })
    });

    const data = await response.json();

    if (response.ok) {
        localStorage.setItem("otp_timer", Date.now() + 60000);
        checkCooldown();
        message.innerText = "OTP resent!";
    } else {
        message.innerText = data.message;
    }
});

resetBtn.addEventListener("click", async () => {
    const studentId = document.getElementById("student_id").value;
    const otp = document.getElementById("otp").value;
    const newPassword = document.getElementById("new_password").value;

    const response = await fetch("/student/reset-password", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            student_id: studentId,
            otp: otp,
            new_password: newPassword
        })
    });

    const data = await response.json();

    if (response.ok) {
        message.style.color = "lightgreen";
        message.innerText = "Password updated successfully!";
        localStorage.removeItem("otp_timer");
        setTimeout(() => {
            window.location.href = "/";
        }, 2000);
    } else {
        message.innerText = data.message;
    }
});
