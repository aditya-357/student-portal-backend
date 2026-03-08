function setActive(element) {
    const items = document.querySelectorAll(".sidebar li");
    items.forEach(item => item.classList.remove("active"));
    element.classList.add("active");
}

async function loadOverview() {
    document.getElementById("content").innerHTML =
        "<h2>Overview</h2><p>Welcome to your portal.</p>";
}


async function logout() {
    const response = await fetch("/student/logout", {
        method: "POST"
    });

    if (response.ok) {
        window.location.href = "/";
    }
}


async function loadAcademic() {
    const response = await fetch("/student/academic");
    const data = await response.json();

    if (!response.ok) {
        document.getElementById("content").innerHTML =
            "<p>Error loading academic data</p>";
        return;
    }

    let semesterList = "";
    data.semester_results.forEach(r => {
        semesterList += `<p>Semester ${r.semester} - SGPA: ${r.sgpa}</p>`;
    });

    const html = `
        <h2>Academic Details</h2>

        <div class="info-card">
            <h3>Course Information</h3>
            <p><strong>Course:</strong> ${data.course}</p>
            <p><strong>Branch:</strong> ${data.branch}</p>
            <p><strong>CGPA:</strong> ${data.cgpa}</p>
        </div>

        <div class="info-card">
            <h3>Semester Results</h3>
            ${semesterList}
        </div>
    `;

    document.getElementById("content").innerHTML = html;
}


async function loadFees(selectedSemester = "") {

    let url = "/student/fees";
    if (selectedSemester) {
        url += `?semester_id=${selectedSemester}`;
    }

    const response = await fetch(url);
    const data = await response.json();

    if (!response.ok) {
        document.getElementById("content").innerHTML =
            "<p>Error loading fee data</p>";
        return;
    }

    const html = `
        <h2>Fees Overview</h2>

        <div class="info-card">
            <h3>Select Semester</h3>
            <select id="semesterSelect" onchange="changeSemester()">
                <option value="">Current Semester</option>
                <option value="1">Semester 1</option>
                <option value="2">Semester 2</option>
                <option value="3">Semester 3</option>
                <option value="4">Semester 4</option>
                <option value="5">Semester 5</option>
                <option value="6">Semester 6</option>
                <option value="7">Semester 7</option>
                <option value="8">Semester 8</option>
            </select>
        </div>

        <div class="info-card">
            <h3>Semester ${data.semester_id} Fees</h3>
            <p><strong>Total Fee:</strong> ₹ ${data.total_fee}</p>
            <p><strong>Paid:</strong> ₹ ${data.paid}</p>
            <p><strong>Due:</strong> ₹ ${data.due}</p>
        </div>

        <div class="info-card">
            <h3>Pay Fees</h3>
            <input type="number" id="payAmount" placeholder="Enter amount" min="1">
            <button onclick="payFees()">Pay Now</button>
            <p id="payMessage"></p>
        </div>

        <div class="info-card">
            <h3>Payment History</h3>
            <div id="paymentHistory">Loading...</div>
        </div>
    `;

    document.getElementById("content").innerHTML = html;

    document.getElementById("semesterSelect").value = selectedSemester;

    loadPaymentHistory();
}

function changeSemester() {
    const semester = document.getElementById("semesterSelect").value;
    loadFees(semester);
}

async function payFees() {
    const amount = parseFloat(document.getElementById("payAmount").value);
    const semester = document.getElementById("semesterSelect").value;
    const message = document.getElementById("payMessage");

    if (!amount || amount <= 0) {
        message.innerText = "Enter valid amount";
        return;
    }

    if (!semester) {
        message.innerText = "Select semester";
        return;
    }

    const response = await fetch("/student/pay", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            amount: amount,
            semester_id: semester
        })
    });

    const data = await response.json();

    if (response.ok) {
        message.style.color = "green";
        message.innerText = "Payment successful!";
        loadFees(semester);
    } else {
        message.style.color = "red";
        message.innerText = data.message;
    }
}


async function loadPaymentHistory() {
    const response = await fetch("/student/payments");
    const data = await response.json();

    if (!response.ok) {
        document.getElementById("paymentHistory").innerHTML =
            "<p>No payment history</p>";
        return;
    }

    let table = `
        <table class="fee-table">
            <tr>
                <th>Semester</th>
                <th>Amount</th>
                <th>Date</th>
            </tr>
    `;

    data.payments.forEach(p => {
        table += `
            <tr>
                <td>${p.semester}</td>
                <td>₹ ${p.amount}</td>
                <td>${p.paid_at}</td>
            </tr>
        `;
    });

    table += "</table>";

    document.getElementById("paymentHistory").innerHTML = table;
}

async function loadHostel() {
    const response = await fetch("/student/hostel");
    const data = await response.json();

    if (!response.ok || data.message) {
        document.getElementById("content").innerHTML =
            "<h2>Hostel</h2><p>No hostel allotted.</p>";
        return;
    }

    const html = `
        <h2>Hostel Details</h2>
        <div class="info-card">
            <h3>Accommodation</h3>
            <p><strong>Hostel Name:</strong> ${data.hostel_name}</p>
            <p><strong>Hostel Type:</strong> ${data.hostel_type}</p>
            <p><strong>Room Number:</strong> ${data.room_no}</p>
        </div>
    `;

    document.getElementById("content").innerHTML = html;
}


async function loadProfile() {
    const response = await fetch("/student/profile");
    const data = await response.json();

    if (!response.ok) {
        document.getElementById("content").innerHTML =
            "<h2>Profile</h2><p>Unable to load profile.</p>";
        return;
    }

    const html = `
        <h2>My Profile</h2>

        <div class="info-card">
            <p><strong>Student ID:</strong> ${data.student_id}</p>
            <p><strong>Name:</strong> ${data.name}</p>
            <p><strong>Email:</strong> ${data.email}</p>
            <p><strong>Date of Birth:</strong> ${data.dob}</p>
            <p><strong>Year of Admission:</strong> ${data.year_of_admission}</p>
        </div>
    `;

    document.getElementById("content").innerHTML = html;
}



async function loadGuardian() {
    const response = await fetch("/student/guardian");
    const data = await response.json();

    if (!response.ok) {
        document.getElementById("content").innerHTML =
            "<h2>Guardian</h2><p>Guardian not assigned.</p>";
        return;
    }

    const html = `
        <h2>Guardian Details</h2>
        <div class="info-card">
            <h3>Guardian Information</h3>
            <p><strong>Name:</strong> ${data.guardian_name}</p>
            <p><strong>Email:</strong> ${data.email}</p>
            <p><strong>Phone:</strong> ${data.phone}</p>
        </div>
    `;

    document.getElementById("content").innerHTML = html;
}

async function loadMentor() {
    const response = await fetch("/student/mentor");
    const data = await response.json();

    if (!response.ok) {
        document.getElementById("content").innerHTML =
            "<h2>Mentor</h2><p>Mentor not assigned.</p>";
        return;
    }

    const html = `
        <h2>Mentor Details</h2>
        <div class="info-card">
            <h3>Mentor Information</h3>
            <p><strong>Name:</strong> ${data.mentor_name}</p>
            <p><strong>Email:</strong> ${data.email}</p>
            <p><strong>Cabin:</strong> ${data.cabin}</p>
        </div>
    `;

    document.getElementById("content").innerHTML = html;
}
