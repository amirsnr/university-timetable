document.addEventListener('DOMContentLoaded', () => {
    document.body.classList.add('login-screen');
    document.getElementById('loginBtn').addEventListener('click', handleLogin);
    document.getElementById('filterBtn').addEventListener('click', filterTimetable);
    document.getElementById('add-timetable-form').addEventListener('submit', defaultFormSubmit);
    document.getElementById('logoutBtn').addEventListener('click', handleLogout);
    document.getElementById('show-register').addEventListener('click', showRegisterForm);
    document.getElementById('register-type-btn').addEventListener('click', toggleRegisterType);
    document.getElementById('register-submit-btn').addEventListener('click', handleRegister);
    document.getElementById('back-to-login').addEventListener('click', backToLogin);

    document.getElementById('register-form').addEventListener('submit', function(e) {
        e.preventDefault();
        handleRegister();
    });
    checkAuthAndSetup();
});


document.addEventListener('DOMContentLoaded', () => {
    // ---- Authentication and UI Setup ----
    document.body.classList.add('login-screen');
    document.getElementById('loginBtn').addEventListener('click', handleLogin);
    document.getElementById('logoutBtn').addEventListener('click', handleLogout);

    // ---- Register Form & Navigation ----
    document.getElementById('show-register').addEventListener('click', showRegisterForm);
    document.getElementById('register-type-btn').addEventListener('click', toggleRegisterType);
    document.getElementById('register-submit-btn').addEventListener('click', handleRegister);
    document.getElementById('back-to-login').addEventListener('click', backToLogin);
    document.getElementById('register-form').addEventListener('submit', function(e) {
        e.preventDefault();
        handleRegister();
    });

    
    document.getElementById('filterBtn').addEventListener('click', filterTimetable);
    document.getElementById('add-timetable-form').addEventListener('submit', defaultFormSubmit);
    document.getElementById('downloadPdfBtn').addEventListener('click', handleDownloadPdf);

    // ---- Initial Auth Check ----
    checkAuthAndSetup();
});

// ============================================================
// Authentication
// ============================================================

function checkAuthAndSetup() {
    const token = localStorage.getItem("token");
    const isAdmin = localStorage.getItem("is_admin") === "true";
    if (token) {
        showAppInterface(isAdmin);
        loadTimetable();
        populateCourseFilterDropdown();
    }
}

function handleLogin() {
    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;
    fetch('/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password })
    })
    .then(response => response.json())
    .then(data => {
        if (data.token && typeof data.is_admin !== "undefined") {
            localStorage.setItem("token", data.token);
            localStorage.setItem("is_admin", data.is_admin);
            showAppInterface(data.is_admin);
            loadTimetable();
        } else {
            alert('Login failed. Invalid credentials.');
        }
    })
    .catch(error => {
        console.error('Login error:', error);
        alert('Login error: ' + error.message);
    });
}

function handleLogout() {
    // Removes authentication info
    localStorage.removeItem('token');
    localStorage.removeItem('is_admin');
    // Updates body class
    document.body.classList.remove('logged-in');
    // Shows login section, hides everything else
    document.getElementById('login-section').style.display = 'block';
    document.getElementById('register-section').style.display = 'none';
    document.getElementById('admin-panel').style.display = 'none';
    document.getElementById('admin-form').style.display = 'none';
    document.getElementById('timetable-container').style.display = 'none';
    document.getElementById('logout-container').style.display = 'none';
    document.getElementById('downloadPdfBtn').style.display = 'none';
    document.querySelector('.filters').style.display = 'none';
    // Resets login form and shows message
    document.getElementById('login-form').reset();
}

function showAppInterface(isAdmin) {
    document.body.classList.remove('login-screen');
    document.body.classList.add('logged-in');
    document.getElementById('logout-container').style.display = 'block';
    document.getElementById('downloadPdfBtn').style.display = 'block';
    document.getElementById('timetable-container').style.display = 'block';
    document.querySelector('.filters').style.display = 'block';
    // Hides login and registes sections
    document.getElementById('login-section').style.display = 'none';
    document.getElementById('register-section').style.display = 'none';
    if (isAdmin) {
        document.getElementById("admin-panel").style.display = "block";
        document.getElementById("admin-form").style.display = "block";
    }
}

// ============================================================
// Registration and Register Form Handling
// ============================================================

function showRegisterForm(e) {
    e.preventDefault();
    document.getElementById('login-section').style.display = 'none';
    document.getElementById('register-section').style.display = 'block';
}

function toggleRegisterType() {
    const btn = document.getElementById('register-type-btn');
    const adminCodeContainer = document.getElementById('admin-code-container');
    if (btn.textContent === 'Register as Admin') {
        btn.textContent = 'Register as Student';
        adminCodeContainer.style.display = 'block';
    } else {
        btn.textContent = 'Register as Admin';
        adminCodeContainer.style.display = 'none';
    }
}

function handleRegister() {
    // Prevents multiple submissions
    const submitBtn = document.getElementById('register-submit-btn');
    submitBtn.disabled = true;
    submitBtn.textContent = 'Processing...';
    const username = document.getElementById('reg-username').value;
    const email = document.getElementById('reg-email').value;
    const password = document.getElementById('reg-password').value;
    const isAdmin = document.getElementById('register-type-btn').textContent === 'Register as Student';
    const adminCode = document.getElementById('admin-code')?.value;
    console.log({ username, email, password, isAdmin, adminCode });
    // Validates admin code if registering as admin
    if (isAdmin && adminCode !== 'unime') {
        showRegisterMessage('Invalid admin code', 'error');
        submitBtn.disabled = false;
        submitBtn.textContent = 'Submit Registration';
        return;
    }
    const endpoint = isAdmin ? '/admin-register' : '/register';
    fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, email, password, admin_code: adminCode })
    })
    .then(response => response.json())
    .then(data => {
        if (data.message) {
            showRegisterMessage(data.message, 'success');
            // Switch back to login after successful registration
            setTimeout(() => {
                document.getElementById('register-section').style.display = 'none';
                document.getElementById('login-section').style.display = 'block';
                document.getElementById('register-form').reset();
                submitBtn.disabled = false;
                submitBtn.textContent = 'Submit Registration';
            }, 1500);
        } else {
            showRegisterMessage(data.error || 'Registration failed', 'error');
            submitBtn.disabled = false;
            submitBtn.textContent = 'Submit Registration';
        }
    })
    .catch(error => {
        showRegisterMessage('Registration error: ' + error.message, 'error');
        submitBtn.disabled = false;
        submitBtn.textContent = 'Submit Registration';
    });
}

function showRegisterMessage(message, type) {
    const msg = document.getElementById('register-message');
    msg.textContent = message;
    msg.className = `message ${type}`;
    setTimeout(() => {
        msg.textContent = '';
        msg.className = '';
    }, 3000);
}

function backToLogin() {
    document.getElementById('register-section').style.display = 'none';
    document.getElementById('login-section').style.display = 'block';
    document.getElementById('register-form').reset();
    document.getElementById('register-message').textContent = '';
}

// ============================================================
// Timetable Management & Utilities
// ============================================================

function loadTimetable(day = '', course = '') {
    const token = localStorage.getItem("token");
    let url = (day || course) ? `/timetable/filter?${new URLSearchParams({ day, course })}` : '/timetable';
    fetch(url, {
        headers: token ? { 'Authorization': 'Bearer ' + token } : {}
    })
    .then(res => res.json())
    .then(data => {
        const entries = data.filtered_timetable || data.timetable || data;
        displayTimetable(entries);
    })
    .catch(err => console.error('Error loading timetable:', err));
}

function displayTimetable(entries) {
    const container = document.getElementById('timetable-container');
    container.innerHTML = '';
    if (!entries || entries.length === 0) {
        container.innerHTML = '<p>No entries found.</p>';
        return;
    }
    const isAdmin = localStorage.getItem("is_admin") === "true";
    const days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'];
    const timeSlots = [
        { time: '09:00-11:00', isBreak: false },
        { time: '11:00-13:00', isBreak: false },
        { time: '13:00-14:00', isBreak: true },
        { time: '14:00-16:00', isBreak: false },
        { time: '16:00-18:00', isBreak: false }
    ];
    const grid = document.createElement('div');
    grid.className = 'timetable-grid';
    // Adds headers
    const cornerCell = document.createElement('div');
    cornerCell.className = 'timetable-header';
    grid.appendChild(cornerCell);
    days.forEach(day => {
        const dayHeader = document.createElement('div');
        dayHeader.className = 'timetable-header';
        dayHeader.textContent = day;
        grid.appendChild(dayHeader);
    });
    // Adds time slots
    timeSlots.forEach(slot => {
        const [startTime, endTime] = slot.time.split('-');
        if (slot.isBreak) {
            const breakCell = document.createElement('div');
            breakCell.className = 'break-row';
            breakCell.textContent = 'Lunch Break';
            grid.appendChild(breakCell);
            return;
        }
        const timeLabel = document.createElement('div');
        timeLabel.className = 'timetable-time';
        timeLabel.textContent = slot.time;
        grid.appendChild(timeLabel);
        days.forEach(day => {
            const cell = document.createElement('div');
            cell.className = 'timetable-cell';
            const matchingEntries = entries.filter(entry => {
                return entry.day_of_week === day &&
                    entry.start_time >= startTime &&
                    entry.end_time <= endTime;
            });
            matchingEntries.forEach(entry => {
                const subjectCard = document.createElement('div');
                subjectCard.className = 'subject-card';
                subjectCard.innerHTML = `
                    <h4>${entry.course_name}</h4>
                    <p>${entry.teacher_name}</p>
                    <p>Room: ${entry.room_number}</p>
                `;
                if (isAdmin) {
                    const adminActions = document.createElement('div');
                    adminActions.className = 'admin-actions';
                    adminActions.innerHTML = `
                        <button onclick="editEntry(${entry.id})">Edit</button>
                        <button onclick="deleteEntry(${entry.id})">Delete</button>
                    `;
                    subjectCard.appendChild(adminActions);
                }
                cell.appendChild(subjectCard);
            });
            grid.appendChild(cell);
        });
    });
    container.appendChild(grid);
}

function populateCourseFilterDropdown() {
    fetch('/api/courses')
        .then(res => res.json())
        .then(courses => {
            const courseSelect = document.getElementById('course');
            courseSelect.innerHTML = '<option value="">All Courses</option>';
            courses.forEach(course => {
                const option = document.createElement('option');
                option.value = course;
                option.textContent = course;
                courseSelect.appendChild(option);
            });
        })
        .catch(err => console.error('Error loading courses for filter:', err));
}

function filterTimetable() {
    const day = document.getElementById('day').value;
    const course = document.getElementById('course').value;
    loadTimetable(day, course);
}

// ============================================================
// Timetable Form Submission (Add/Update)
// ============================================================

function defaultFormSubmit(e) {
    e.preventDefault();
    const formData = {
        day_of_week: document.getElementById("dayOfWeek").value,
        start_time: document.getElementById("startTime").value,
        course_name: document.getElementById("courseName").value,
        room_number: document.getElementById("roomNumber").value,
        teacher_name: document.getElementById("teacherName").value
    };
    // Auto-set end time
    const endMap = {
        "09:00": "11:00",
        "11:00": "13:00",
        "14:00": "16:00",
        "16:00": "18:00"
    };
    formData.end_time = endMap[formData.start_time] || formData.start_time;
    const token = localStorage.getItem("token");
    fetch("/timetable", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + token
        },
        body: JSON.stringify(formData)
    })
    .then(res => res.json())
    .then(data => {
        if (data.error) {
            alert(data.message || "Error adding timetable");
            return;
        }
        alert("Entry added successfully!");
        loadTimetable();
        document.getElementById("add-timetable-form").reset();
    })
    .catch(err => {
        console.error("Error adding timetable:", err);
        alert("Error: " + err.message);
    });
}

function editEntry(id) {
    document.getElementById("admin-panel").style.display = "block";
    document.getElementById("admin-form").style.display = "block";
    // Scroll to admin panel
    document.getElementById("admin-panel").scrollIntoView({ behavior: "smooth" });
    const subjectCard = document.querySelector(`button[onclick="editEntry(${id})"]`).closest(".subject-card");
    const course = subjectCard.querySelector("h4").textContent;
    const teacher = subjectCard.querySelector("p:nth-child(2)").textContent;
    const room = subjectCard.querySelector("p:nth-child(3)").textContent.replace("Room: ", "");
    const cell = subjectCard.closest(".timetable-cell");
    const day = cell.parentElement.querySelector(".timetable-header").textContent;
    const timeRange = cell.parentElement.querySelector(".timetable-time").textContent;
    const [startTime, endTime] = timeRange.split("-");
    document.getElementById("courseName").value = course;
    document.getElementById("teacherName").value = teacher;
    document.getElementById("roomNumber").value = room;
    document.getElementById("dayOfWeek").value = day;
    document.getElementById("startTime").value = startTime.trim();
    const submitBtn = document.querySelector("#add-timetable-form button");
    submitBtn.textContent = "Update Timetable";
    document.getElementById("add-timetable-form").removeEventListener('submit', defaultFormSubmit);
    document.getElementById("add-timetable-form").onsubmit = function(e) {
        e.preventDefault();
        updateTimetable(id);
    };
}

function updateTimetable(id) {
    const formData = {
        day_of_week: document.getElementById("dayOfWeek").value,
        start_time: document.getElementById("startTime").value,
        course_name: document.getElementById("courseName").value,
        room_number: document.getElementById("roomNumber").value,
        teacher_name: document.getElementById("teacherName").value
    };
    const endMap = {
        "09:00": "11:00",
        "11:00": "13:00",
        "14:00": "16:00",
        "16:00": "18:00"
    };
    formData.end_time = endMap[formData.start_time] || formData.start_time;
    const token = localStorage.getItem("token");
    fetch(`/timetable/${id}`, {
        method: "PUT",
        headers: {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + token
        },
        body: JSON.stringify(formData)
    })
    .then(res => res.json())
    .then(data => {
        if (data.error) {
            alert(data.message || "Error updating timetable");
            return;
        }
        alert("Entry updated successfully!");
        loadTimetable();
        document.getElementById("add-timetable-form").reset();
        document.getElementById("add-timetable-form").onsubmit = defaultFormSubmit;
        document.querySelector("#add-timetable-form button").textContent = "Add Timetable";
    })
    .catch(err => {
        console.error("Error updating timetable:", err);
        alert("Error: " + err.message);
    });
}

function deleteEntry(id) {
    if (!confirm("Are you sure you want to delete this entry?")) return;
    const token = localStorage.getItem("token");
    fetch(`/timetable/${id}`, {
        method: "DELETE",
        headers: {
            "Authorization": "Bearer " + token
        }
    })
    .then(res => res.json())
    .then(data => {
        alert(data.message || "Entry deleted");
        loadTimetable();
    })
    .catch(err => {
        console.error("Error deleting entry:", err);
        alert("Error deleting entry");
    });
}


function handleDownloadPdf() {
    const timetable = document.getElementById('timetable-container');
    timetable.scrollIntoView(); // ensures it's fully rendered
    html2canvas(timetable, { scale: 2 }).then(canvas => {
        const imgData = canvas.toDataURL('image/png');
        const pdf = new jspdf.jsPDF('p', 'mm', 'a4');
        const pdfWidth = pdf.internal.pageSize.getWidth();
        const pdfHeight = canvas.height * pdfWidth / canvas.width;
        pdf.addImage(imgData, 'PNG', 0, 0, pdfWidth, pdfHeight);
        pdf.save('timetable.pdf');
    });
}
