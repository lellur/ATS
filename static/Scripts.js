// Collect and send files to Flask backend
async function uploadAndScan() {
  const resumes = resumeInput.files;
  const jd = jdInput.files[0];

  if (!jd || resumes.length === 0) {
    alert("Please upload both JD and at least one resume.");
    return;
  }

  const formData = new FormData();
  formData.append("jd", jd);
  for (let i = 0; i < resumes.length; i++) {
    formData.append("resumes", resumes[i]);
  }

  // Show loading message
  const outputBox = document.getElementById('outputBox');
  outputBox.innerHTML = "<div>Processing, please wait...</div>";

  try {
    const response = await fetch("/api/upload", {
      method: "POST",
      body: formData
    });
    if (!response.ok) throw new Error("Server error");
    const data = await response.json();
    // Expecting data.results or similar structure from backend
    renderResults(data.results || []);
  } catch (err) {
    outputBox.innerHTML = "<div style='color:red;'>Error: " + err.message + "</div>";
  }
}

// Trigger upload when both files are selected
resumeInput.addEventListener('change', () => {
  if (jdInput.files.length > 0 && resumeInput.files.length > 0) {
    uploadAndScan();
  }
});
jdInput.addEventListener('change', () => {
  if (jdInput.files.length > 0 && resumeInput.files.length > 0) {
    uploadAndScan();
  }
});