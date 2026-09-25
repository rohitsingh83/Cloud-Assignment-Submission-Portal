// ============================================================================
// Cloud-Based Student Assignment Submission & Feedback Portal
// Frontend Single Page Application Engine (Vanilla JS + Modern Async/Await)
// ============================================================================

// Global Application State
const state = {
  token: localStorage.getItem("token") || null,
  user: JSON.parse(localStorage.getItem("user") || "null"),
  assignments: [],
  courses: [],
  teacherSubmissions: [],
  selectedFile: null
};

// Dynamic Cloud API Base Resolution:
// Uses same-origin relative URLs on localhost/Render monolithic, or auto-detects Render backend when on Vercel
function getApiBase() {
  if (window.API_BASE_OVERRIDE) return window.API_BASE_OVERRIDE;
  const stored = localStorage.getItem("EDUCLOUD_API_BASE");
  if (stored) return stored.replace(/\/+$/, "");
  const host = window.location.hostname;
  if (host === "localhost" || host === "127.0.0.1" || host === "") {
    return "";
  }
  // When hosted on Vercel Edge or Netlify, default to Render deployment endpoint
  if (host.includes("vercel.app") || host.includes("netlify.app")) {
    return "https://cloud-assignment-portal-backend.onrender.com";
  }
  return "";
}

const API_BASE = getApiBase();

// ----------------- TOAST NOTIFICATIONS -----------------
function showToast(message, type = "info") {
  const container = document.getElementById("toastContainer");
  if (!container) return;

  const toast = document.createElement("div");
  toast.className = `p-3 px-4 rounded-xl shadow-lg text-xs font-semibold flex items-center space-x-2 text-white pointer-events-auto transition transform translate-y-2 duration-300`;

  let icon = "fa-circle-info";
  if (type === "success") {
    toast.classList.add("bg-emerald-600");
    icon = "fa-circle-check";
  } else if (type === "error") {
    toast.classList.add("bg-rose-600");
    icon = "fa-circle-exclamation";
  } else if (type === "warning") {
    toast.classList.add("bg-amber-600");
    icon = "fa-triangle-exclamation";
  } else {
    toast.classList.add("bg-indigo-600");
  }

  toast.innerHTML = `<i class="fa-solid ${icon}"></i> <span>${escapeHtml(message)}</span>`;
  container.appendChild(toast);

  setTimeout(() => {
    toast.classList.add("opacity-0");
    setTimeout(() => toast.remove(), 400);
  }, 3500);
}

// ----------------- AUTHENTICATION -----------------
function switchAuthTab(tab) {
  const loginBtn = document.getElementById("loginTabBtn");
  const regBtn = document.getElementById("registerTabBtn");
  const loginForm = document.getElementById("loginForm");
  const regForm = document.getElementById("registerForm");

  if (tab === "login") {
    loginBtn.className = "flex-1 py-3 text-center text-sm font-bold border-b-2 border-indigo-600 text-indigo-600 bg-indigo-50/50";
    regBtn.className = "flex-1 py-3 text-center text-sm font-semibold text-slate-500 hover:text-slate-700";
    loginForm.classList.remove("hidden");
    regForm.classList.add("hidden");
  } else {
    regBtn.className = "flex-1 py-3 text-center text-sm font-bold border-b-2 border-indigo-600 text-indigo-600 bg-indigo-50/50";
    loginBtn.className = "flex-1 py-3 text-center text-sm font-semibold text-slate-500 hover:text-slate-700";
    regForm.classList.remove("hidden");
    loginForm.classList.add("hidden");
  }
}

function fillDemoCredentials(email, password) {
  switchAuthTab("login");
  document.getElementById("loginEmail").value = email;
  document.getElementById("loginPassword").value = password;
}

async function handleLogin(e) {
  e.preventDefault();
  const email = document.getElementById("loginEmail").value.trim();
  const password = document.getElementById("loginPassword").value;

  try {
    const res = await fetch(`${API_BASE}/api/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password })
    });
    const data = await res.json();

    if (!res.ok) {
      throw new Error(data.detail || "Authentication failed");
    }

    state.token = data.access_token;
    state.user = data.user;
    localStorage.setItem("token", state.token);
    localStorage.setItem("user", JSON.stringify(state.user));

    showToast(`Signed in as ${state.user.name} (${state.user.role})`, "success");
    initApp();
  } catch (err) {
    showToast(err.message, "error");
  }
}

async function handleRegister(e) {
  e.preventDefault();
  const name = document.getElementById("regName").value.trim();
  const email = document.getElementById("regEmail").value.trim();
  const password = document.getElementById("regPassword").value;
  const role = document.getElementById("regRole").value;

  try {
    const res = await fetch(`${API_BASE}/api/auth/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, email, password, role })
    });
    const data = await res.json();

    if (!res.ok) {
      throw new Error(data.detail || "Registration failed");
    }

    showToast("Registration successful! Please sign in with your credentials.", "success");
    switchAuthTab("login");
    document.getElementById("loginEmail").value = email;
    document.getElementById("loginPassword").value = "";
  } catch (err) {
    showToast(err.message, "error");
  }
}

function logout() {
  state.token = null;
  state.user = null;
  localStorage.removeItem("token");
  localStorage.removeItem("user");
  showToast("Logged out successfully", "info");
  renderView();
}

// ----------------- VIEW ROUTING -----------------
function renderView() {
  const authNav = document.getElementById("authNavProfile");
  const authSec = document.getElementById("authSection");
  const studentSec = document.getElementById("studentSection");
  const teacherSec = document.getElementById("teacherSection");

  if (!state.token || !state.user) {
    authNav.classList.add("hidden");
    authNav.classList.remove("flex");
    authSec.classList.remove("hidden");
    studentSec.classList.add("hidden");
    teacherSec.classList.add("hidden");
    return;
  }

  // User is logged in
  authNav.classList.remove("hidden");
  authNav.classList.add("flex");
  authSec.classList.add("hidden");

  document.getElementById("navUserName").textContent = state.user.name;
  document.getElementById("navUserRole").textContent = state.user.role;

  if (state.user.role === "teacher" || state.user.role === "admin") {
    studentSec.classList.add("hidden");
    teacherSec.classList.remove("hidden");
    document.getElementById("teacherDisplayName").textContent = state.user.name;
    loadTeacherDashboard();
  } else {
    teacherSec.classList.add("hidden");
    studentSec.classList.remove("hidden");
    document.getElementById("studentDisplayName").textContent = state.user.name;
    loadStudentDashboard();
  }
}

// ----------------- STUDENT WORKFLOWS -----------------
function switchStudentTab(tab) {
  const assignBtn = document.getElementById("studentTabAssignBtn");
  const subsBtn = document.getElementById("studentTabSubsBtn");
  const assignList = document.getElementById("studentAssignmentsList");
  const subsList = document.getElementById("studentSubmissionsList");

  if (tab === "assignments") {
    assignBtn.className = "pb-2 text-sm font-extrabold border-b-2 border-indigo-600 text-indigo-600 transition flex items-center";
    subsBtn.className = "pb-2 text-sm font-semibold text-slate-500 hover:text-slate-800 transition flex items-center";
    assignList.classList.remove("hidden");
    subsList.classList.add("hidden");
  } else {
    subsBtn.className = "pb-2 text-sm font-extrabold border-b-2 border-indigo-600 text-indigo-600 transition flex items-center";
    assignBtn.className = "pb-2 text-sm font-semibold text-slate-500 hover:text-slate-800 transition flex items-center";
    subsList.classList.remove("hidden");
    assignList.classList.add("hidden");
    loadStudentSubmissions();
  }
}

async function loadStudentDashboard() {
  try {
    const res = await fetch(`${API_BASE}/api/dashboard/student`, {
      headers: { "Authorization": `Bearer ${state.token}` }
    });
    if (res.status === 401) { logout(); return; }
    const stats = await res.json();

    document.getElementById("statStudentTotal").textContent = stats.total_assignments;
    document.getElementById("statStudentPending").textContent = stats.pending_assignments;
    document.getElementById("statStudentSubmitted").textContent = stats.submitted_assignments;
    document.getElementById("statStudentLate").textContent = stats.late_assignments;
    document.getElementById("statStudentGraded").textContent = stats.graded_assignments;

    loadStudentAssignments();
  } catch (err) {
    showToast("Error loading student stats", "error");
  }
}

async function loadStudentAssignments() {
  try {
    const res = await fetch(`${API_BASE}/api/assignments`, {
      headers: { "Authorization": `Bearer ${state.token}` }
    });
    state.assignments = await res.json();
    renderStudentAssignments(state.assignments);
  } catch (err) {
    showToast("Error loading assignments", "error");
  }
}

function filterStudentAssignments() {
  const searchInput = document.getElementById("studentSearchInput");
  const search = (searchInput ? searchInput.value : "").toLowerCase().trim();
  if (!search) {
    renderStudentAssignments(state.assignments);
    return;
  }
  const filtered = state.assignments.filter(a => {
    return (a.title && a.title.toLowerCase().includes(search)) ||
           (a.description && a.description.toLowerCase().includes(search)) ||
           (a.course_code && a.course_code.toLowerCase().includes(search));
  });
  renderStudentAssignments(filtered);
}

function renderStudentAssignments(assignments) {
  const container = document.getElementById("studentAssignmentsList");
  if (!assignments || assignments.length === 0) {
    container.innerHTML = `<div class="col-span-2 text-center p-8 bg-white rounded-xl border border-slate-200 text-slate-500 text-sm">No assignments posted yet.</div>`;
    return;
  }

  container.innerHTML = assignments.map(a => {
    const deadlineDate = new Date(a.deadline);
    const isPast = new Date() > deadlineDate;

    let statusBadge = `<span class="badge-status badge-pending"><i class="fa-regular fa-clock"></i> Pending</span>`;
    if (a.has_submitted) {
      if (a.submission_status === "LATE") {
        statusBadge = `<span class="badge-status badge-late"><i class="fa-solid fa-triangle-exclamation"></i> Late Submission</span>`;
      } else if (a.submission_status === "GRADED") {
        statusBadge = `<span class="badge-status badge-graded"><i class="fa-solid fa-check-double"></i> Graded: ${a.student_marks}/${a.max_marks}</span>`;
      } else {
        statusBadge = `<span class="badge-status badge-submitted"><i class="fa-solid fa-circle-check"></i> Submitted</span>`;
      }
    }

    return `
      <div class="bg-white rounded-2xl shadow-sm border border-slate-200 p-5 flex flex-col justify-between space-y-4">
        <div>
          <div class="flex items-center justify-between gap-2 mb-2">
            <span class="text-xs font-semibold px-2 py-0.5 bg-indigo-50 text-indigo-700 rounded-md border border-indigo-100">${escapeHtml(a.course_code || 'CS-401')}</span>
            ${statusBadge}
          </div>
          <h3 class="font-bold text-base text-slate-900">${escapeHtml(a.title)}</h3>
          <p class="text-xs text-slate-600 mt-2 line-clamp-3 leading-relaxed">${escapeHtml(a.description || 'No description provided.')}</p>
        </div>

        <div class="border-t border-slate-100 pt-3 space-y-2 text-xs text-slate-500">
          <div class="flex justify-between items-center">
            <span><i class="fa-regular fa-calendar mr-1"></i> Deadline:</span>
            <span class="font-medium ${isPast ? 'text-rose-600 font-bold' : 'text-slate-800'}">${deadlineDate.toLocaleString()}</span>
          </div>
          <div class="flex justify-between items-center">
            <span><i class="fa-solid fa-award mr-1"></i> Maximum Marks:</span>
            <span class="font-medium text-slate-800">${a.max_marks} pts</span>
          </div>
          <div class="flex justify-between items-center">
            <span><i class="fa-solid fa-file-lines mr-1"></i> Allowed Formats:</span>
            <span class="uppercase text-indigo-700 font-semibold">${escapeHtml(a.allowed_file_types)}</span>
          </div>
        </div>

        <button onclick="openSubmitModal('${a.assignment_id}', '${escapeHtml(a.title)}', '${a.allowed_file_types}')" class="w-full ${a.has_submitted ? 'bg-slate-100 hover:bg-slate-200 text-slate-800' : 'bg-indigo-600 hover:bg-indigo-700 text-white shadow-md shadow-indigo-600/20'} text-xs font-bold py-2.5 rounded-xl transition flex items-center justify-center">
          <i class="fa-solid ${a.has_submitted ? 'fa-arrows-rotate' : 'fa-upload'} mr-1.5"></i>
          ${a.has_submitted ? 'Resubmit Assignment' : 'Submit Assignment'}
        </button>
      </div>
    `;
  }).join("");
}

async function loadStudentSubmissions() {
  const container = document.getElementById("studentSubmissionsList");
  try {
    const res = await fetch(`${API_BASE}/api/submissions/me`, {
      headers: { "Authorization": `Bearer ${state.token}` }
    });
    const subs = await res.json();

    if (!subs || subs.length === 0) {
      container.innerHTML = `<div class="text-center p-8 bg-white rounded-2xl border border-slate-200 text-slate-500 text-sm">You haven't submitted any assignments yet.</div>`;
      return;
    }

    container.innerHTML = subs.map(s => {
      const isGraded = s.submission_status === "GRADED";
      return `
        <div class="bg-white rounded-2xl p-5 shadow-sm border border-slate-200 space-y-4">
          <div class="flex flex-col sm:flex-row justify-between sm:items-center gap-3">
            <div>
              <span class="text-xs font-bold text-indigo-600 uppercase tracking-wider">${escapeHtml(s.course_code || 'CS-401')}</span>
              <h4 class="font-bold text-base text-slate-900">${escapeHtml(s.assignment_title)}</h4>
              <p class="text-xs text-slate-500">Submitted: ${new Date(s.submitted_at).toLocaleString()}</p>
            </div>
            <div class="flex items-center space-x-2">
              <span class="badge-status ${s.submission_status === 'LATE' ? 'badge-late' : s.submission_status === 'GRADED' ? 'badge-graded' : 'badge-submitted'}">
                ${s.submission_status}
              </span>
              <button onclick="openPreviewModal('${s.submission_id}', '${escapeHtml(s.file_name)}')" class="bg-indigo-50 hover:bg-indigo-100 border border-indigo-200 text-indigo-700 text-xs px-3 py-1.5 rounded-xl transition font-semibold">
                <i class="fa-solid fa-eye mr-1"></i> Preview
              </button>
              <button onclick="downloadFile('${s.submission_id}')" class="bg-slate-100 hover:bg-slate-200 border border-slate-200 text-slate-700 text-xs px-3 py-1.5 rounded-xl transition font-medium">
                <i class="fa-solid fa-download mr-1"></i> Download
              </button>
            </div>
          </div>

          <!-- Feedback & Marks Card -->
          <div class="bg-slate-50 border border-slate-200 rounded-xl p-4">
            <div class="flex justify-between items-center mb-2">
              <span class="text-xs font-bold text-slate-700 uppercase"><i class="fa-solid fa-chalkboard-user mr-1 text-indigo-600"></i> Faculty Evaluation</span>
              <span class="text-sm font-extrabold ${isGraded ? 'text-indigo-600' : 'text-slate-400'}">
                ${isGraded ? `Marks: ${s.marks} / ${s.max_marks}` : 'Evaluation Pending'}
              </span>
            </div>
            <p class="text-xs text-slate-600 leading-relaxed italic">
              ${s.feedback ? `"${escapeHtml(s.feedback)}"` : (isGraded ? 'No written feedback comments provided.' : 'Your submission has been securely written to cloud object storage and is waiting for instructor review.')}
            </p>
          </div>
        </div>
      `;
    }).join("");
  } catch (err) {
    showToast("Error loading submission history", "error");
  }
}

// ----------------- SUBMIT MODAL (Student) -----------------
function openSubmitModal(assignmentId, title, allowedTypes) {
  document.getElementById("submitModalAssignmentId").value = assignmentId;
  document.getElementById("submitModalAssignmentTitle").textContent = title;
  document.getElementById("submitModalAllowedTypes").textContent = `Allowed formats: ${allowedTypes.toUpperCase()} (Max 25MB)`;
  document.getElementById("submitFileInput").value = "";
  document.getElementById("selectedFileName").classList.add("hidden");
  state.selectedFile = null;

  document.getElementById("submitModal").classList.remove("hidden");
}

function closeSubmitModal() {
  document.getElementById("submitModal").classList.add("hidden");
}

// Drag & drop handlers
const dropZone = document.getElementById("dropZone");
if (dropZone) {
  dropZone.addEventListener("click", () => document.getElementById("submitFileInput").click());
  dropZone.addEventListener("dragover", (e) => { e.preventDefault(); dropZone.classList.add("border-indigo-600", "bg-indigo-100/50"); });
  dropZone.addEventListener("dragleave", () => { dropZone.classList.remove("border-indigo-600", "bg-indigo-100/50"); });
  dropZone.addEventListener("drop", (e) => {
    e.preventDefault();
    dropZone.classList.remove("border-indigo-600", "bg-indigo-100/50");
    if (e.dataTransfer.files.length > 0) {
      processSelectedFile(e.dataTransfer.files[0]);
    }
  });
}

function handleFileSelected(input) {
  if (input.files.length > 0) {
    processSelectedFile(input.files[0]);
  }
}

function processSelectedFile(file) {
  state.selectedFile = file;
  const nameLabel = document.getElementById("selectedFileName");
  nameLabel.textContent = `Selected: ${file.name} (${(file.size / (1024 * 1024)).toFixed(2)} MB)`;
  nameLabel.classList.remove("hidden");
}

function attachSampleFile() {
  const samplePdfContent = `%PDF-1.4
1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj
2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj
3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >> endobj
4 0 obj << /Length 75 >> stream
BT
/F1 18 Tf
50 720 Td
(Cloud Assignment Portal - Verified Student Submission) Tj
ET
endstream endobj
5 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj
xref
0 6
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000244 00000 n 
0000000370 00000 n 
trailer << /Size 6 /Root 1 0 R >>
startxref
449
%%EOF`;

  const blob = new Blob([samplePdfContent], { type: "application/pdf" });
  const sampleFile = new File([blob], "verified_cloud_solution.pdf", { type: "application/pdf" });
  processSelectedFile(sampleFile);
  showToast("Attached verified sample PDF solution for instant testing!", "success");
}

async function handleUploadSubmission(e) {
  e.preventDefault();
  if (!state.selectedFile) {
    showToast("Please choose a file to upload", "warning");
    return;
  }

  const assignmentId = document.getElementById("submitModalAssignmentId").value;
  const submitBtn = document.getElementById("uploadSubmitBtn");
  submitBtn.disabled = true;
  submitBtn.innerHTML = `<i class="fa-solid fa-spinner fa-spin mr-1.5"></i> Streaming to Cloud...`;

  const formData = new FormData();
  formData.append("file", state.selectedFile);

  try {
    const res = await fetch(`${API_BASE}/api/assignments/${assignmentId}/submit`, {
      method: "POST",
      headers: { "Authorization": `Bearer ${state.token}` },
      body: formData
    });
    const data = await res.json();

    if (!res.ok) {
      throw new Error(data.detail || "Submission upload failed");
    }

    showToast(`Assignment submitted successfully! Status: ${data.submission_status}`, "success");
    closeSubmitModal();
    loadStudentDashboard();
  } catch (err) {
    showToast(err.message, "error");
  } finally {
    submitBtn.disabled = false;
    submitBtn.innerHTML = `<i class="fa-solid fa-cloud-arrow-up mr-2"></i> Upload to Cloud Storage`;
  }
}

// ----------------- TEACHER WORKFLOWS -----------------
async function loadTeacherDashboard() {
  try {
    const res = await fetch(`${API_BASE}/api/dashboard/teacher`, {
      headers: { "Authorization": `Bearer ${state.token}` }
    });
    if (res.status === 401) { logout(); return; }
    const stats = await res.json();

    document.getElementById("statTeacherTotalAssign").textContent = stats.total_assignments;
    document.getElementById("statTeacherTotalSubs").textContent = stats.total_submissions;
    document.getElementById("statTeacherPending").textContent = stats.pending_reviews;
    document.getElementById("statTeacherLate").textContent = stats.late_submissions;
    document.getElementById("statTeacherGraded").textContent = stats.graded_submissions;

    await loadTeacherAssignments();
    await loadAllSubmissionsForTeacher();
  } catch (err) {
    showToast("Error loading faculty analytics", "error");
  }
}

async function loadTeacherAssignments() {
  try {
    const res = await fetch(`${API_BASE}/api/assignments`, {
      headers: { "Authorization": `Bearer ${state.token}` }
    });
    state.assignments = await res.json();

    // Populate filter dropdown
    const filterSelect = document.getElementById("teacherAssignmentFilter");
    filterSelect.innerHTML = `<option value="ALL">All Assignments (${state.assignments.length})</option>` +
      state.assignments.map(a => `<option value="${a.assignment_id}">${escapeHtml(a.title)}</option>`).join("");
  } catch (err) {
    showToast("Error loading assignments for teacher", "error");
  }
}

async function loadAllSubmissionsForTeacher() {
  const tbody = document.getElementById("teacherSubmissionsTableBody");
  tbody.innerHTML = `<tr><td colspan="7" class="py-6 text-center text-xs text-slate-400">Loading submissions from Cloud Object Storage...</td></tr>`;

  try {
    let allSubs = [];
    for (const a of state.assignments) {
      const res = await fetch(`${API_BASE}/api/assignments/${a.assignment_id}/submissions`, {
        headers: { "Authorization": `Bearer ${state.token}` }
      });
      if (res.ok) {
        const subs = await res.json();
        allSubs = allSubs.concat(subs);
      }
    }

    state.teacherSubmissions = allSubs;
    renderTeacherSubmissionsTable(state.teacherSubmissions);
  } catch (err) {
    showToast("Error loading submissions", "error");
  }
}

function filterTeacherSubmissions() {
  const selected = document.getElementById("teacherAssignmentFilter").value;
  if (selected === "ALL") {
    renderTeacherSubmissionsTable(state.teacherSubmissions);
  } else {
    const filtered = state.teacherSubmissions.filter(s => s.assignment_id === selected);
    renderTeacherSubmissionsTable(filtered);
  }
}

function renderTeacherSubmissionsTable(submissions) {
  const tbody = document.getElementById("teacherSubmissionsTableBody");
  if (!submissions || submissions.length === 0) {
    tbody.innerHTML = `<tr><td colspan="7" class="py-8 text-center text-xs text-slate-500">No submissions found matching criteria.</td></tr>`;
    return;
  }

  tbody.innerHTML = submissions.map(s => {
    let statusClass = "badge-submitted";
    if (s.submission_status === "LATE") statusClass = "badge-late";
    if (s.submission_status === "GRADED") statusClass = "badge-graded";

    return `
      <tr class="hover:bg-slate-50/80 transition">
        <td class="py-3.5 px-4">
          <div class="font-bold text-slate-900">${escapeHtml(s.student_name || 'Student')}</div>
          <div class="text-xs text-slate-400">${escapeHtml(s.student_email || '-')}</div>
        </td>
        <td class="py-3.5 px-4 font-semibold text-slate-800">${escapeHtml(s.assignment_title)}</td>
        <td class="py-3.5 px-4 text-xs text-slate-500">${new Date(s.submitted_at).toLocaleString()}</td>
        <td class="py-3.5 px-4">
          <span class="badge-status ${statusClass}">${s.submission_status}</span>
        </td>
        <td class="py-3.5 px-4 font-bold text-slate-800">
          ${s.marks !== null ? `${s.marks} / ${s.max_marks}` : '<span class="text-slate-400 font-normal">Ungraded</span>'}
        </td>
        <td class="py-3.5 px-4">
          <div class="flex items-center space-x-1.5">
            <button onclick="openPreviewModal('${s.submission_id}', '${escapeHtml(s.file_name)}')" class="bg-indigo-50 hover:bg-indigo-100 text-indigo-700 text-xs px-2.5 py-1 rounded-lg border border-indigo-200 transition font-semibold flex items-center" title="Inline In-Browser Document Preview">
              <i class="fa-solid fa-eye mr-1"></i> Preview
            </button>
            <button onclick="downloadFile('${s.submission_id}')" class="bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs px-2 py-1 rounded-lg border border-slate-300 transition font-medium flex items-center" title="Download from Cloud Storage">
              <i class="fa-solid fa-download"></i>
            </button>
          </div>
          <div class="text-[11px] text-slate-400 mt-1 truncate max-w-[130px]">${escapeHtml(truncateString(s.file_name, 16))}</div>
        </td>
        <td class="py-3.5 px-4 text-right">
          <div class="flex items-center justify-end space-x-2">
            <button onclick="openSimilarityModal('${s.submission_id}', '${escapeHtml(s.student_name)}', '${escapeHtml(s.assignment_title)}')" class="bg-purple-50 hover:bg-purple-100 text-purple-700 text-xs px-2.5 py-1.5 rounded-lg border border-purple-200 transition font-semibold flex items-center" title="Scan for Plagiarism and Peer Similarity">
              <i class="fa-solid fa-wand-magic-sparkles mr-1"></i> Similarity
            </button>
            <button onclick="openGradeModal('${s.submission_id}', '${escapeHtml(s.student_name)}', '${escapeHtml(s.assignment_title)}', ${s.max_marks}, ${s.marks ?? 'null'}, '${escapeHtml(s.feedback || '')}')" class="bg-indigo-600 hover:bg-indigo-700 text-white text-xs px-3 py-1.5 rounded-lg transition font-semibold flex items-center shadow-sm">
              <i class="fa-solid fa-pen-to-square mr-1"></i> Grade
            </button>
          </div>
        </td>
      </tr>
    `;
  }).join("");
}

// ----------------- CREATE ASSIGNMENT MODAL (Teacher) -----------------
async function openCreateAssignmentModal() {
  const courseSelect = document.getElementById("createAssignCourse");
  courseSelect.innerHTML = `<option value="">Loading courses...</option>`;

  try {
    const res = await fetch(`${API_BASE}/api/assignments/courses`, {
      headers: { "Authorization": `Bearer ${state.token}` }
    });
    const courses = await res.json();
    courseSelect.innerHTML = courses.map(c => `<option value="${c.course_id}">${c.course_code} - ${c.course_name}</option>`).join("");
  } catch (err) {
    showToast("Error loading courses", "error");
  }

  // Set default deadline to 7 days from now
  const now = new Date();
  now.setDate(now.getDate() + 7);
  now.setMinutes(now.getMinutes() - now.getTimezoneOffset());
  document.getElementById("createAssignDeadline").value = now.toISOString().slice(0, 16);

  document.getElementById("createAssignmentModal").classList.remove("hidden");
}

function closeCreateAssignmentModal() {
  document.getElementById("createAssignmentModal").classList.add("hidden");
}

async function handleCreateAssignment(e) {
  e.preventDefault();
  const course_id = document.getElementById("createAssignCourse").value;
  const title = document.getElementById("createAssignTitle").value.trim();
  const description = document.getElementById("createAssignDesc").value.trim();
  const deadlineLocal = document.getElementById("createAssignDeadline").value;
  const max_marks = parseInt(document.getElementById("createAssignMarks").value);
  const allowed_file_types = document.getElementById("createAssignTypes").value.trim();
  const max_file_size_mb = parseInt(document.getElementById("createAssignSize").value);

  const deadlineISO = new Date(deadlineLocal).toISOString();

  try {
    const res = await fetch(`${API_BASE}/api/assignments`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${state.token}`
      },
      body: JSON.stringify({
        course_id,
        title,
        description,
        deadline: deadlineISO,
        max_marks,
        allowed_file_types,
        max_file_size_mb
      })
    });
    const data = await res.json();

    if (!res.ok) {
      throw new Error(data.detail || "Failed to create assignment");
    }

    showToast("Assignment published successfully!", "success");
    closeCreateAssignmentModal();
    loadTeacherDashboard();
  } catch (err) {
    showToast(err.message, "error");
  }
}

// ----------------- GRADE MODAL (Teacher) -----------------
function openGradeModal(submissionId, studentName, assignmentTitle, maxMarks, currentMarks, currentFeedback) {
  document.getElementById("gradeModalSubmissionId").value = submissionId;
  document.getElementById("gradeModalStudentMeta").textContent = `Student: ${studentName} | Task: ${assignmentTitle}`;
  document.getElementById("gradeModalMaxMarks").textContent = maxMarks;

  const marksInput = document.getElementById("gradeModalMarksInput");
  marksInput.max = maxMarks;
  marksInput.value = currentMarks !== null ? currentMarks : "";

  document.getElementById("gradeModalFeedbackInput").value = currentFeedback || "";
  document.getElementById("gradeModal").classList.remove("hidden");
}

function closeGradeModal() {
  document.getElementById("gradeModal").classList.add("hidden");
}

async function handleSaveGrade(e) {
  e.preventDefault();
  const submissionId = document.getElementById("gradeModalSubmissionId").value;
  const marks = parseFloat(document.getElementById("gradeModalMarksInput").value);
  const feedback = document.getElementById("gradeModalFeedbackInput").value.trim();

  try {
    const res = await fetch(`${API_BASE}/api/submissions/${submissionId}/grade`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${state.token}`
      },
      body: JSON.stringify({ marks, feedback })
    });
    const data = await res.json();

    if (!res.ok) {
      throw new Error(data.detail || "Grading submission failed");
    }

    showToast("Grade and written feedback saved to cloud database!", "success");
    closeGradeModal();
    loadTeacherDashboard();
  } catch (err) {
    showToast(err.message, "error");
  }
}

// ----------------- PREVIEW MODAL -----------------
function openPreviewModal(submissionId, filename) {
  const modal = document.getElementById("previewModal");
  const title = document.getElementById("previewModalTitle");
  const iframe = document.getElementById("previewIframe");
  const fallback = document.getElementById("previewFallback");
  const dlBtn = document.getElementById("previewModalDownloadBtn");

  title.textContent = `Preview: ${filename}`;
  dlBtn.onclick = () => downloadFile(submissionId);

  // Set iframe src using token parameter for secure session authentication
  const previewUrl = `${API_BASE}/api/submissions/${submissionId}/preview?token=${encodeURIComponent(state.token)}`;
  iframe.src = previewUrl;
  iframe.classList.remove("hidden");
  fallback.classList.add("hidden");

  modal.classList.remove("hidden");
}

function closePreviewModal() {
  const modal = document.getElementById("previewModal");
  const iframe = document.getElementById("previewIframe");
  iframe.src = "about:blank";
  modal.classList.add("hidden");
}

// ----------------- SIMILARITY / PLAGIARISM MODAL -----------------
async function openSimilarityModal(submissionId, studentName, assignmentTitle) {
  const modal = document.getElementById("similarityModal");
  const meta = document.getElementById("similarityModalMeta");
  const loading = document.getElementById("similarityLoading");
  const content = document.getElementById("similarityContent");

  meta.textContent = `Student: ${studentName} | Assignment: ${assignmentTitle}`;
  loading.classList.remove("hidden");
  content.classList.add("hidden");
  modal.classList.remove("hidden");

  try {
    const res = await fetch(`${API_BASE}/api/submissions/${submissionId}/similarity-check`, {
      headers: { "Authorization": `Bearer ${state.token}` }
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Plagiarism scanner failed");
    }

    const data = await res.json();
    loading.classList.add("hidden");
    content.classList.remove("hidden");

    const scoreEl = document.getElementById("similarityScoreText");
    const riskBadge = document.getElementById("similarityRiskBadge");
    const verdictEl = document.getElementById("similarityVerdict");
    const matchesList = document.getElementById("similarityMatchesList");

    scoreEl.textContent = `${data.max_similarity_score.toFixed(1)}%`;
    if (data.risk_color === "rose") {
      scoreEl.className = "text-3xl font-black text-rose-600 mt-0.5";
      riskBadge.className = "badge-status badge-late text-xs";
    } else if (data.risk_color === "amber") {
      scoreEl.className = "text-3xl font-black text-amber-600 mt-0.5";
      riskBadge.className = "badge-status badge-pending text-xs";
    } else {
      scoreEl.className = "text-3xl font-black text-emerald-600 mt-0.5";
      riskBadge.className = "badge-status badge-submitted text-xs";
    }
    riskBadge.textContent = data.risk_level;
    verdictEl.textContent = data.verdict;

    if (!data.matches || data.matches.length === 0) {
      matchesList.innerHTML = `<div class="text-xs text-slate-400 italic">No other submissions found for comparison.</div>`;
    } else {
      matchesList.innerHTML = data.matches.map(m => `
        <div class="flex items-center justify-between p-2.5 rounded-xl border border-slate-200 bg-white text-xs">
          <div>
            <div class="font-bold text-slate-800">${escapeHtml(m.peer_student_name || 'Anonymous Student')}</div>
            <div class="text-[11px] text-slate-400">${escapeHtml(m.peer_file_name)}</div>
          </div>
          <span class="font-bold px-2 py-0.5 rounded-md ${m.similarity_score > 60 ? 'bg-rose-100 text-rose-700' : m.similarity_score > 30 ? 'bg-amber-100 text-amber-800' : 'bg-emerald-100 text-emerald-800'}">
            ${m.similarity_score.toFixed(1)}% Match
          </span>
        </div>
      `).join("");
    }
  } catch (err) {
    loading.classList.add("hidden");
    showToast(err.message, "error");
    closeSimilarityModal();
  }
}

function closeSimilarityModal() {
  document.getElementById("similarityModal").classList.add("hidden");
}

// ----------------- CSV GRADE EXPORT -----------------
async function exportCurrentGradesCSV() {
  const filterSelect = document.getElementById("teacherAssignmentFilter");
  let assignmentId = filterSelect ? filterSelect.value : "ALL";

  if (assignmentId === "ALL") {
    if (state.assignments && state.assignments.length > 0) {
      assignmentId = state.assignments[0].assignment_id;
    } else {
      showToast("No assignments available to export", "warning");
      return;
    }
  }

  try {
    const res = await fetch(`${API_BASE}/api/assignments/${assignmentId}/export-csv`, {
      headers: { "Authorization": `Bearer ${state.token}` }
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "CSV Export failed");
    }

    const blob = await res.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `grade_report_${assignmentId.slice(0, 8)}.csv`;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    a.remove();

    showToast("Grades CSV exported successfully!", "success");
  } catch (err) {
    showToast(err.message, "error");
  }
}

// ----------------- FILE DOWNLOAD HELPER -----------------
async function downloadFile(submissionId) {
  try {
    const res = await fetch(`${API_BASE}/api/submissions/${submissionId}/download?token=${encodeURIComponent(state.token)}`);

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Download failed");
    }

    const disposition = res.headers.get("content-disposition");
    let filename = "submission_file";
    if (disposition && disposition.indexOf("filename=") !== -1) {
      const parts = disposition.split("filename=");
      filename = parts[1].replace(/['"]/g, "").trim();
    }

    const blob = await res.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    a.remove();

    showToast("File downloaded from cloud storage", "info");
  } catch (err) {
    showToast(err.message, "error");
  }
}

// ----------------- UTILITY HELPERS -----------------
function escapeHtml(str) {
  if (!str) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function truncateString(str, num) {
  if (!str) return "";
  if (str.length <= num) return str;
  return str.slice(0, num) + "...";
}

// Initialize Application
function initApp() {
  renderView();
}

window.addEventListener("DOMContentLoaded", initApp);
