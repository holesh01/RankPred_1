function goHome() {
  window.location.href = "index.html";
}

const statusMsg = document.getElementById("statusMsg");

const params = new URLSearchParams(window.location.search);
const exam = params.get("exam");
const roll = params.get("roll");

if (!exam || !roll) {
  statusMsg.textContent = "Result details not provided.";
} else {
  fetch(
    `http://127.0.0.1:5000/result?exam=${encodeURIComponent(exam)}&roll=${encodeURIComponent(roll)}`
  )
    .then(res => res.json())
    .then(data => {
      if (data.error) {
        statusMsg.textContent = data.error;
        return;
      }

      // ---------- BASIC INFO ----------
      statusMsg.style.display = "none";

      document.getElementById("examName").textContent =
        data.exam.replaceAll("_", " ");

      document.getElementById("rName").textContent =
        data.candidate.name;

      document.getElementById("rRoll").textContent =
        data.candidate.roll;

      document.getElementById("rCategory").textContent =
        data.candidate.category;

      document.getElementById("rState").textContent =
        data.candidate.state;

      // ---------- EXAM DATE & SHIFT TIME ----------
      const shift = parseShift(data.shift_id);

      const examDateEl = document.getElementById("examDate");
      const shiftTimeEl = document.getElementById("shiftTime");

      if (examDateEl) examDateEl.textContent = shift.date;
      if (shiftTimeEl) shiftTimeEl.textContent = shift.time;

      // ---------- SUBJECT TABLE ----------
      const body = document.getElementById("subjectTableBody");
      body.innerHTML = "";

      // counted subjects
      data.counted_subjects.forEach(sub => {
        const tr = document.createElement("tr");
        tr.classList.add("row-counted");

        tr.innerHTML = `
          <td>${sub.name}</td>
          <td>${sub.attempt}</td>
          <td>${sub.na}</td>
          <td>${sub.r}</td>
          <td>${sub.w}</td>
          <td>${sub.marks}</td>
        `;
        body.appendChild(tr);
      });

      // qualifying subjects
      data.qualifying_subjects.forEach(sub => {
        const tr = document.createElement("tr");
        tr.classList.add("row-qualifying");

        tr.innerHTML = `
          <td>${sub.name} <span class="qual-tag">(Qualifying)</span></td>
          <td>${sub.attempt}</td>
          <td>${sub.na}</td>
          <td>${sub.r}</td>
          <td>${sub.w}</td>
          <td>${sub.marks}</td>
        `;
        body.appendChild(tr);
      });

      // ---------- FINAL MARKS ----------
      document.getElementById("finalMarks").textContent = data.final_marks;

      // ---------- SHIFT RANK ----------
      const rankEl = document.getElementById("shiftRank");
      const totalEl = document.getElementById("totalCandidates");

      if (
        data.candidate.rank !== undefined &&
        data.candidate.rank !== null &&
        data.total_candidates
      ) {
        rankEl.textContent = data.candidate.rank;
        totalEl.textContent = data.total_candidates;
      } else {
        rankEl.textContent = "-";
        totalEl.textContent = "-";
      }
    })
    .catch(err => {
      console.error(err);
      statusMsg.textContent =
        "Result not available yet. Please try again later.";
    });
}

function downloadPDF() {
  const params = new URLSearchParams(window.location.search);
  const exam = params.get("exam");
  const roll = params.get("roll");

  if (!exam || !roll) {
    alert("Missing exam or roll");
    return;
  }

  window.open(
    `http://127.0.0.1:5000/result-pdf?exam=${encodeURIComponent(exam)}&roll=${encodeURIComponent(roll)}`,
    "_blank"
  );
}

// ---------- SHIFT PARSER ----------
function parseShift(shiftId) {
  if (!shiftId) return { date: "-", time: "-" };

  const parts = shiftId.split("_");

  return {
    date: parts[0].replaceAll("-", "/"),
    time: parts.slice(1).join(" ").replaceAll("-", ":")
  };
}
