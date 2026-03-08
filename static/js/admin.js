function showSection(section) {

    const content = document.getElementById("content-area");

    if (section === "search") {
        content.innerHTML = `
            <h2>Search Student</h2>
            <input type="text" id="studentId" placeholder="Enter Student ID">
            <button onclick="searchStudent()">Search</button>
            <div id="result"></div>
        `;
    }

    if (section === "add") {
        content.innerHTML = `
            <h2>Add Student</h2>

            <div class="form-grid">
                <input type="text" id="new_id" placeholder="Student ID">
                <input type="text" id="new_name" placeholder="Name">
                <input type="date" id="new_dob">
                <input type="email" id="new_email" placeholder="Email">

                <input type="text" id="new_year" placeholder="Year of Admission">
                <input type="text" id="new_branch" placeholder="Branch ID">
                <input type="number" id="new_gender" placeholder="Gender ID">

                <input type="text" id="new_mentor" placeholder="Mentor ID">
                <input type="number" id="new_semester" placeholder="Current Semester ID">
            </div>

            <button onclick="addStudent()">Add Student</button>

            <div id="addResult"></div>
        `;
    }

   if (section === "allocate") {
    content.innerHTML = `
        <h2>Allocate Hostel</h2>

        <div class="form-grid">
            <input type="text" id="alloc_student" placeholder="Student ID">

            <select id="alloc_hostel">
                <option value="">Select Hostel</option>
                <option value="qc-2">qc-2</option>
                <option value="kp-14">kp-14</option>
                <option value="kp-25E">kp-25E</option>
                <option value="qc-5">qc-5</option>
                <option value="kp-25A">kp-25A</option>
            </select>

            <input type="text" id="alloc_room" placeholder="Room No">
        </div>

        <button onclick="allocateHostel()">Allocate</button>

        <div id="allocateResult"></div>
    `;
}



    if (section === "delete") {
    content.innerHTML = `
        <h2>Delete Student</h2>

        <input type="text" id="delete_id" placeholder="Enter Student ID">
        <button onclick="deleteStudent()">Delete</button>

        <div id="deleteResult"></div>
    `;
}

if (section === "update") {
    content.innerHTML = `
        <h2>Update Student</h2>

        <input type="text" id="update_id" placeholder="Enter Student ID"><br><br>

        <select id="update_field">
            <option value="">Select Field</option>
            <option value="name">Name</option>
            <option value="email">Email</option>
        </select><br><br>

        <input type="text" id="update_value" placeholder="Enter New Value"><br><br>

        <button onclick="updateStudent()">Update</button>

        <div id="updateResult"></div>
    `;
}


}

async function updateStudent() {

    const studentId = document.getElementById("update_id").value;
    const field = document.getElementById("update_field").value;
    const value = document.getElementById("update_value").value;
    const resultDiv = document.getElementById("updateResult");

    if (!studentId || !field || !value) {
        resultDiv.innerHTML = `<p style="color:red">All fields required</p>`;
        return;
    }

    const response = await fetch("/admin/update-student-field", {
        method: "PUT",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            student_id: studentId,
            field: field,
            value: value
        })
    });

    const data = await response.json();

    if (!response.ok) {
        resultDiv.innerHTML = `<p style="color:red">${data.message || data.error}</p>`;
        return;
    }

    resultDiv.innerHTML = `<p style="color:green">${data.message}</p>`;
}


async function deleteStudent() {

    const studentId = document.getElementById("delete_id").value;
    const resultDiv = document.getElementById("deleteResult");

    if (!studentId) {
        resultDiv.innerHTML = `<p style="color:red">Student ID required</p>`;
        return;
    }

    // Confirmation popup
    const confirmDelete = confirm("Are you sure you want to delete this student?");
    if (!confirmDelete) return;

    const response = await fetch(`/admin/delete-student/${studentId}`, {
        method: "DELETE"
    });

    const data = await response.json();

    if (!response.ok) {
        resultDiv.innerHTML = `<p style="color:red">${data.message || data.error}</p>`;
        return;
    }

    resultDiv.innerHTML = `<p style="color:green">${data.message}</p>`;
}



async function searchStudent() {

    const studentId = document.getElementById("studentId").value;

    if (!studentId) {
        alert("Enter Student ID");
        return;
    }

    const response = await fetch(`/admin/full-student/${studentId}`);
    const data = await response.json();

    const resultDiv = document.getElementById("result");

    if (!response.ok) {
        resultDiv.innerHTML = `<p style="color:red">${data.message}</p>`;
        return;
    }

    resultDiv.innerHTML = `
    <div class="details-card">
        <h3>Student Details</h3>

        <div class="details-grid">
            <div><span>Name</span><p>${data.name}</p></div>
            <div><span>Email</span><p>${data.email}</p></div>

            <div><span>DOB</span><p>${data.dob}</p></div>
            <div><span>Year</span><p>${data.year_of_admission}</p></div>

            <div><span>Course</span><p>${data.course}</p></div>
            <div><span>Branch</span><p>${data.branch}</p></div>

            <div><span>Semester</span><p>${data.semester}</p></div>
            <div><span>Mentor</span><p>${data.mentor}</p></div>

            <div><span>Guardian</span><p>${data.guardian}</p></div>
            <div><span>Hostel</span><p>${data.hostel}</p></div>

            <div><span>Room</span><p>${data.room}</p></div>
        </div>
    </div>
`;
}

async function allocateHostel() {

    const studentId = document.getElementById("alloc_student").value;
    const hostelId = document.getElementById("alloc_hostel").value;
    const roomNo = document.getElementById("alloc_room").value;
    const resultDiv = document.getElementById("allocateResult");

    if (!studentId || !hostelId || !roomNo) {
        resultDiv.innerHTML = `<p style="color:red">All fields required</p>`;
        return;
    }

    const response = await fetch("/admin/allocate-hostel", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            student_id: studentId,
            hostel_id: hostelId,
            room_no: roomNo
        })
    });

    const data = await response.json();

    if (!response.ok) {
        resultDiv.innerHTML = `<p style="color:red">${data.message || data.error}</p>`;
        return;
    }

    resultDiv.innerHTML = `<p style="color:green">${data.message}</p>`;
}


async function addStudent() {

    const payload = {
        student_id: document.getElementById("new_id").value,
        name: document.getElementById("new_name").value,
        dob: document.getElementById("new_dob").value,
        email: document.getElementById("new_email").value,
        year_of_admission: document.getElementById("new_year").value,
        branch_id: document.getElementById("new_branch").value,
        gender_id: parseInt(document.getElementById("new_gender").value),
        mentor_id: document.getElementById("new_mentor").value,
        current_semester_id: parseInt(document.getElementById("new_semester").value)
    };

    const response = await fetch("/admin/add-student", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
    });

    const data = await response.json();
    const resultDiv = document.getElementById("addResult");

    if (!response.ok) {
        resultDiv.innerHTML = `<p style="color:red">${data.message || data.error}</p>`;
        return;
    }

    resultDiv.innerHTML = `<p style="color:green">${data.message}</p>`;
}





async function logoutAdmin() {
    await fetch("/admin/logout", { method: "POST" });
    window.location.href = "/";
}
