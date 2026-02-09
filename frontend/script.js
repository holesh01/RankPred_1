// // // ---------------- NAVIGATION ----------------
// // function goBack() {
// //   window.location.href = "index.html";
// // }

// // // ---------------- LOAD EXAM ----------------
// // document.addEventListener("DOMContentLoaded", () => {
// //   const exam = localStorage.getItem("selectedExam");
// //   const title = document.getElementById("examTitle");
// //   if (title && exam) {
// //     title.textContent = exam + " Evaluation";
// //   }
// // });

// // // ---------------- SUBMIT EVALUATION ----------------
// // async function submitEvaluation() {
// //   const exam = localStorage.getItem("selectedExam");

// //   const fileInput = document.getElementById("responseFile");
// //   const urlInput = document.getElementById("resultUrl");

// //   const category = document.getElementById("category").value;
// //   const gender = document.getElementById("gender").value;
// //   const state = document.getElementById("state").value;

// //   const statusEl = document.getElementById("status");
// //   statusEl.textContent = "";

// //   if (!exam || !category || !gender || !state) {
// //     alert("Please select Category, Gender and State");
// //     return;
// //   }

// //   const hasFile = fileInput && fileInput.files.length > 0;
// //   const hasUrl = urlInput && urlInput.value.trim() !== "";

// //   if (!hasFile && !hasUrl) {
// //     alert("Upload response file OR paste DigiALM result link");
// //     return;
// //   }

// //   statusEl.textContent = "Evaluating...";

// //   try {
// //     let res;

// //     // ---------------- FILE FLOW (OPTIONAL / LEGACY) ----------------
// //     if (hasFile) {
// //       const formData = new FormData();
// //       formData.append("exam_name", exam);
// //       formData.append("category", category);
// //       formData.append("gender", gender);
// //       formData.append("state", state);
// //       formData.append("file", fileInput.files[0]);

// //       res = await fetch("http://127.0.0.1:5000/evaluate", {
// //         method: "POST",
// //         body: formData
// //       });

// //     // ---------------- URL FLOW (PRIMARY) ----------------
// //     } else {
// //       res = await fetch("http://127.0.0.1:5000/evaluate-from-url", {
// //         method: "POST",
// //         headers: { "Content-Type": "application/json" },
// //         body: JSON.stringify({
// //           exam_name: exam,
// //           category,
// //           gender,
// //           state,
// //           url: urlInput.value.trim()
// //         })
// //       });
// //     }

// //     const data = await res.json();

// //     if (!res.ok) {
// //       throw new Error(data.error || "Evaluation failed");
// //     }

// //     statusEl.textContent = "Evaluation saved successfully";

// //     // 🔥 Roll number comes from backend extraction
// //     const roll = data.candidate?.roll;
// //     if (!roll) {
// //       throw new Error("Roll number not found in response sheet");
// //     }

// //     // ✅ Redirect AFTER success
// //     window.location.href =
// //       `result.html?exam=${encodeURIComponent(exam)}&roll=${encodeURIComponent(roll)}`;

// //   } catch (err) {
// //     console.error(err);
// //     statusEl.textContent = "Evaluation failed: " + err.message;
// //   }
// // }

// // ---------------- NAVIGATION ----------------
// function goBack() {
//   window.location.href = "index.html";
// }

// // ---------------- LOAD EXAM ----------------
// document.addEventListener("DOMContentLoaded", () => {
//   const exam = localStorage.getItem("selectedExam");
//   const title = document.getElementById("examTitle");
//   if (title && exam) {
//     title.textContent = exam + " Evaluation";
//   }
// });

// // ---------------- SUBMIT EVALUATION (HTML UPLOAD ONLY) ----------------
// async function submitEvaluation() {
//   const exam = localStorage.getItem("selectedExam");

//   const fileInput = document.getElementById("responseFile");
//   const category = document.getElementById("category").value;
//   const gender = document.getElementById("gender").value;
//   const state = document.getElementById("state").value;

//   const statusEl = document.getElementById("status");
//   statusEl.textContent = "";

//   if (!exam || !category || !gender || !state) {
//     alert("Please select Category, Gender and State");
//     return;
//   }

//   if (!fileInput || fileInput.files.length === 0) {
//     alert("Please upload DigiALM response HTML file");
//     return;
//   }

//   statusEl.textContent = "Evaluating response sheet...";

//   try {
//     const formData = new FormData();
//     formData.append("exam_name", exam);
//     formData.append("category", category);
//     formData.append("gender", gender);
//     formData.append("state", state);
//     formData.append("file", fileInput.files[0]);

//     const res = await fetch("https://rankpred-1.onrender.com/evaluate", {
//       method: "POST",
//       body: formData
//     });

//     const data = await res.json();

//     if (!res.ok) {
//       throw new Error(data.error || "Evaluation failed");
//     }

//     statusEl.textContent = "Evaluation saved successfully";

//     const roll = data.roll;
//     if (!roll) {
//       throw new Error("Roll number not returned from server");
//     }

//     // ✅ Redirect to result page
//     window.location.href =
//       `result.html?exam=${encodeURIComponent(exam)}&roll=${encodeURIComponent(roll)}`;

//   } catch (err) {
//     console.error(err);
//     statusEl.textContent = "Evaluation failed: " + err.message;
//   }
// }
// fetch("https://rankpred-1.onrender.com/admin/create-exam", {
//   method: "POST",
//   headers: {
//     "Content-Type": "application/json",
//     "X-ADMIN-KEY": "Abc@1183"
//   },
//   body: JSON.stringify(data)
// });

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
