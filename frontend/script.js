// ---------------- NAVIGATION ----------------
function goBack() {
  window.location.href = "index.html";
}

// ---------------- LOAD EXAM ----------------
document.addEventListener("DOMContentLoaded", () => {
  const exam = localStorage.getItem("selectedExam");
  const title = document.getElementById("examTitle");
  if (title && exam) {
    title.textContent = exam + " Evaluation";
  }
});

// ---------------- SUBMIT EVALUATION (OPTION 1) ----------------
async function submitEvaluation() {
  const exam = localStorage.getItem("selectedExam");

  const fileInput = document.getElementById("responseFile");
  const urlInput = document.getElementById("resultUrl");

  const category = document.getElementById("category").value;
  const gender = document.getElementById("gender").value;
  const state = document.getElementById("state").value;

  const statusEl = document.getElementById("status");
  statusEl.textContent = "";

  if (!exam || !category || !gender || !state) {
    alert("Please select Category, Gender and State");
    return;
  }

  const hasFile = fileInput && fileInput.files.length > 0;
  const hasUrl = urlInput && urlInput.value.trim() !== "";

  if (!hasFile && !hasUrl) {
    alert("Upload HTML file OR paste DigiALM result link");
    return;
  }

  statusEl.textContent = "Evaluating response sheet...";

  try {
    let fileToSend;

    // ---------- FILE UPLOAD FLOW ----------
    if (hasFile) {
      fileToSend = fileInput.files[0];
    }
    // ---------- URL → HTML FLOW (OPTION 1) ----------
    else {
      const pageRes = await fetch(urlInput.value.trim());
      if (!pageRes.ok) {
        throw new Error("Unable to fetch result page");
      }

      const html = await pageRes.text();
      const blob = new Blob([html], { type: "text/html" });
      fileToSend = new File([blob], "result.html", {
        type: "text/html"
      });
    }

    const formData = new FormData();
    formData.append("exam_name", exam);
    formData.append("category", category);
    formData.append("gender", gender);
    formData.append("state", state);
    formData.append("file", fileToSend);

    const res = await fetch("https://rankpred-1.onrender.com/evaluate", {
      method: "POST",
      body: formData
    });

    const data = await res.json();

    if (!res.ok) {
      throw new Error(data.error || "Evaluation failed");
    }

    statusEl.textContent = "Evaluation saved successfully";

    const roll = data.roll;
    if (!roll) {
      throw new Error("Roll number not returned from server");
    }

    // ---------- REDIRECT TO RESULT ----------
    window.location.href =
      `result.html?exam=${encodeURIComponent(exam)}&roll=${encodeURIComponent(roll)}`;

  } catch (err) {
    console.error(err);
    statusEl.textContent = "Evaluation failed: " + err.message;
  }
}
