

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
import shutil
import re
from bs4 import BeautifulSoup
from openpyxl import Workbook, load_workbook
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import io

app = Flask(__name__)
CORS(app)

BASE_DIR = "data"
UPLOAD_DIR = "uploads"

os.makedirs(BASE_DIR, exist_ok=True)
os.makedirs(UPLOAD_DIR, exist_ok=True)

from functools import wraps

def require_admin(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        key = request.headers.get("X-ADMIN-KEY")
        if key != os.getenv("ADMIN_KEY"):
            return jsonify({"error": "Unauthorized"}), 401
        return f(*args, **kwargs)
    return wrapper

# ---------------- BASIC ----------------
@app.route("/")
def home():
    return "Backend running"

def safe_name(name):
    return name.replace(" ", "_")

def make_shift_id(exam_date, exam_time):
    date_part = exam_date.replace("/", "-")
    time_part = exam_time.replace(":", "-")
    time_part = re.sub(r"\s+", "", time_part)
    return f"{date_part}_{time_part}"

# ---------------- ADMIN: LIST EXAMS ----------------
@app.route("/admin/exams", methods=["GET"])
def admin_list_exams():
    exams = []
    for folder in os.listdir(BASE_DIR):
        exam_dir = os.path.join(BASE_DIR, folder)
        scheme_path = os.path.join(exam_dir, "marking_scheme.xlsx")
        if not os.path.exists(scheme_path):
            continue

        wb = load_workbook(scheme_path)
        ws = wb.active
        scheme = {r[0]: r[1] for r in ws.iter_rows(min_row=2, values_only=True)}

        exams.append({
            "exam_name": scheme.get("Exam Name"),
            "correct": scheme.get("Correct"),
            "wrong": scheme.get("Wrong"),
            "na": scheme.get("NA")
        })
    return jsonify(exams)

# ---------------- ADMIN: CREATE EXAM ----------------
@app.route("/admin/create-exam", methods=["POST"])
def create_exam():
    data = request.json
    exam_name = data.get("exam_name")
    subjects = data.get("subjects", [])
    correct = data.get("correct")
    wrong = data.get("wrong")
    na = data.get("na")

    if not exam_name or not subjects:
        return jsonify({"error": "Invalid data"}), 400

    exam_dir = os.path.join(BASE_DIR, safe_name(exam_name))
    os.makedirs(exam_dir, exist_ok=True)

    # marking scheme
    wb = Workbook()
    ws = wb.active
    ws.append(["Key", "Value"])
    ws.append(["Exam Name", exam_name])
    ws.append(["Correct", correct])
    ws.append(["Wrong", wrong])
    ws.append(["NA", na])
    wb.save(os.path.join(exam_dir, "marking_scheme.xlsx"))

    # subjects
    wb2 = Workbook()
    ws2 = wb2.active
    ws2.append(["Subject Name", "Max Marks", "Count In Total"])
    for s in subjects:
        ws2.append([s["name"], s["max_marks"], "YES" if s["count_in_total"] else "NO"])
    wb2.save(os.path.join(exam_dir, "subjects.xlsx"))

    # responses template
    wb3 = Workbook()
    ws3 = wb3.active
    header = ["Name", "Roll", "Category", "Gender", "State", "Final Marks"]
    for s in subjects:
        base = s["name"]
        header += [f"{base}_Attempt", f"{base}_R", f"{base}_W", f"{base}_NA", f"{base}_Marks"]
    ws3.append(header)
    wb3.save(os.path.join(exam_dir, "responses.xlsx"))

    return jsonify({"status": "success"})

# ---------------- ADMIN: DELETE EXAM ----------------
@app.route("/admin/delete-exam", methods=["POST"])
def delete_exam():
    exam = request.json.get("exam_name")
    path = os.path.join(BASE_DIR, safe_name(exam))
    if not os.path.exists(path):
        return jsonify({"error": "Exam not found"}), 404
    shutil.rmtree(path)
    return jsonify({"status": "deleted"})

# ---------------- READ HELPERS ----------------
def read_marking_scheme(exam):
    wb = load_workbook(os.path.join(BASE_DIR, safe_name(exam), "marking_scheme.xlsx"))
    return {r[0]: r[1] for r in wb.active.iter_rows(min_row=2, values_only=True)}

def read_subjects(exam):
    wb = load_workbook(os.path.join(BASE_DIR, safe_name(exam), "subjects.xlsx"))
    return [{
        "name": r[0],
        "count_in_total": r[2] == "YES"
    } for r in wb.active.iter_rows(min_row=2, values_only=True)]

# ---------------- PARSE RESPONSE HTML ----------------
def parse_response_html(html, scheme, subjects):
    soup = BeautifulSoup(html, "lxml")
    section_map = {}
    order = []
    current = None

    for el in soup.find_all("div"):
        if el.get("class") == ["section-lbl"]:
            current = el.get_text(strip=True)
            section_map[current] = {"c": 0, "w": 0, "n": 0}
            order.append(current)

        if el.get("class") == ["question-pnl"] and current:
            chosen = None
            correct = None

            ch = el.find("td", string=re.compile("Chosen Option"))
            if ch:
                v = ch.find_next_sibling("td").get_text(strip=True)
                if v != "--":
                    chosen = int(v)

            rt = el.find("td", class_="rightAns")
            if rt:
                m = re.search(r"(\d)\.", rt.get_text())
                if m:
                    correct = int(m.group(1))

            if chosen is None:
                section_map[current]["n"] += 1
            elif chosen == correct:
                section_map[current]["c"] += 1
            else:
                section_map[current]["w"] += 1

    results = []
    final = 0

    for i, sec in enumerate(order):
        c = section_map[sec]["c"]
        w = section_map[sec]["w"]
        n = section_map[sec]["n"]

        marks = c * scheme["Correct"] + w * scheme["Wrong"] + n * scheme["NA"]
        sub = subjects[i]

        results.append({
            "name": sub["name"],
            "attempt": c + w,
            "r": c,
            "w": w,
            "na": n,
            "marks": marks,
            "count_in_total": sub["count_in_total"]
        })

        if sub["count_in_total"]:
            final += marks

    return final, results

# ---------------- SAVE RESULT ----------------
def save_user_result(exam_name, shift_id, base_data, subject_results):
    exam_dir = os.path.join(BASE_DIR, safe_name(exam_name))
    path = os.path.join(exam_dir, f"responses_{shift_id}.xlsx")

    # create shift file from template if not exists
    if not os.path.exists(path):
        template = os.path.join(exam_dir, "responses.xlsx")
        shutil.copy(template, path)

    wb = load_workbook(path)
    ws = wb.active

    headers = [c.value for c in ws[1]]
    col_index = {h: i for i, h in enumerate(headers)}

    roll_value = base_data[col_index["Roll"]]
    updated = False

    # 🔁 CHECK EXISTING ROLL
    for row_idx in range(2, ws.max_row + 1):
        existing_roll = ws.cell(row=row_idx, column=col_index["Roll"] + 1).value
        if str(existing_roll) == str(roll_value):
            # UPDATE EXISTING ROW
            for key in ["Name", "Category", "Gender", "State", "Final Marks"]:
                ws.cell(
                    row=row_idx,
                    column=col_index[key] + 1,
                    value=base_data[col_index[key]]
                )

            for sub in subject_results:
                base = sub["name"]
                ws.cell(row=row_idx, column=col_index[f"{base}_Attempt"] + 1, value=sub["attempt"])
                ws.cell(row=row_idx, column=col_index[f"{base}_R"] + 1, value=sub["r"])
                ws.cell(row=row_idx, column=col_index[f"{base}_W"] + 1, value=sub["w"])
                ws.cell(row=row_idx, column=col_index[f"{base}_NA"] + 1, value=sub["na"])
                ws.cell(row=row_idx, column=col_index[f"{base}_Marks"] + 1, value=sub["marks"])

            updated = True
            break

    # ➕ ADD NEW ROW IF ROLL NOT FOUND
    if not updated:
        row = base_data[:]
        for sub in subject_results:
            row.extend([sub["attempt"], sub["r"], sub["w"], sub["na"], sub["marks"]])
        ws.append(row)

    wb.save(path)
    calculate_shift_ranks(path)


# ---------------- EVALUATE (HTML UPLOAD) ----------------
@app.route("/evaluate", methods=["POST"])
def evaluate():
    exam = request.form.get("exam_name")
    category = request.form.get("category")
    gender = request.form.get("gender")
    state = request.form.get("state")
    file = request.files.get("file")

    if not all([exam, category, gender, state, file]):
        return jsonify({"error": "Missing fields"}), 400

    html = file.read().decode("utf-8", errors="ignore")

    scheme = read_marking_scheme(exam)
    subjects = read_subjects(exam)

    soup = BeautifulSoup(html, "lxml")
    text = soup.get_text(" ")

    date = re.search(r"\d{2}/\d{2}/\d{4}", text).group()
    time = re.search(r"\d{1,2}:\d{2}\s*(AM|PM)\s*-\s*\d{1,2}:\d{2}\s*(AM|PM)", text).group()

    shift = make_shift_id(date, time)

    name = soup.find("td", string=re.compile("Candidate Name")).find_next_sibling("td").get_text(strip=True)
    roll = soup.find("td", string=re.compile("Roll")).find_next_sibling("td").get_text(strip=True)

    final, subject_results = parse_response_html(html, scheme, subjects)

    save_user_result(
        exam,
        shift,
        [name, roll, category, gender, state, final],
        subject_results
    )

    return jsonify({"status": "saved", "roll": roll})

# ---------------- RESULT API ----------------
@app.route("/result")
def get_result():
    exam = request.args.get("exam")
    roll = request.args.get("roll")

    exam_dir = os.path.join(BASE_DIR, safe_name(exam))
    subjects_cfg = read_subjects(exam)

    for file in os.listdir(exam_dir):
        if not file.startswith("responses_"):
            continue

        path = os.path.join(exam_dir, file)
        wb = load_workbook(path)
        ws = wb.active
        headers = [c.value for c in ws[1]]
        col = {h: i for i, h in enumerate(headers)}

        total_candidates = ws.max_row - 1

        for r in ws.iter_rows(min_row=2, values_only=True):
            if str(r[col["Roll"]]) == str(roll):
                shift_id = file.replace("responses_", "").replace(".xlsx", "")
                counted, qualifying, final = [], [], 0

                for sub in subjects_cfg:
                    base = sub["name"]
                    item = {
                        "name": base,
                        "attempt": r[col[f"{base}_Attempt"]],
                        "na": r[col[f"{base}_NA"]],
                        "r": r[col[f"{base}_R"]],
                        "w": r[col[f"{base}_W"]],
                        "marks": r[col[f"{base}_Marks"]]
                    }
                    if sub["count_in_total"]:
                        counted.append(item)
                        final += item["marks"]
                    else:
                        qualifying.append(item)

                return jsonify({
                    "exam": exam,
                    "shift_id": shift_id,
                    "candidate": {
                        "name": r[col["Name"]],
                        "roll": r[col["Roll"]],
                        "category": r[col["Category"]],
                        "gender": r[col["Gender"]],
                        "state": r[col["State"]],
                        "rank": r[col.get("Rank")]
                    },
                    "total_candidates": total_candidates,
                    "counted_subjects": counted,
                    "qualifying_subjects": qualifying,
                    "final_marks": final
                })

    return jsonify({"error": "Candidate not found"}), 404

# ---------------- RANK ----------------
def calculate_shift_ranks(path):
    wb = load_workbook(path)
    ws = wb.active
    headers = [c.value for c in ws[1]]
    col = {h: i for i, h in enumerate(headers)}

    if "Rank" not in col:
        ws.cell(1, len(headers) + 1, "Rank")
        col["Rank"] = len(headers)

    rows = [(r, ws.cell(r, col["Final Marks"] + 1).value)
            for r in range(2, ws.max_row + 1)]
    rows.sort(key=lambda x: x[1], reverse=True)

    rank = 1
    prev = None
    count = 0
    for r, m in rows:
        if m != prev:
            rank = count + 1
        ws.cell(r, col["Rank"] + 1, rank)
        prev = m
        count += 1

    wb.save(path)

@app.route("/result-pdf")
def result_pdf():
    exam = request.args.get("exam")
    roll = request.args.get("roll")

    if not exam or not roll:
        return jsonify({"error": "Missing exam or roll"}), 400

    # reuse existing result logic
    result = get_result().get_json()
    if "error" in result:
        return jsonify(result), 400

    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    # ---------- WATERMARK ----------
    c.saveState()
    c.setFont("Helvetica-Bold", 60)
    c.setFillGray(0.9)
    c.translate(width / 2, height / 2)
    c.rotate(45)
    c.drawCentredString(0, 0, "RankPred")
    c.restoreState()

    y = height - 50

    # ---------- HEADER ----------
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(width / 2, y, result["exam"])
    y -= 30

    # ---------- CANDIDATE DETAILS ----------
    c.setFont("Helvetica", 11)
    cand = result["candidate"]

    details = [
        f"Name: {cand['name']}",
        f"Roll No: {cand['roll']}",
        f"Category: {cand['category']}",
        f"State: {cand['state']}"
    ]

    for d in details:
        c.drawString(50, y, d)
        y -= 15

    y -= 15

    # ---------- TABLE CONFIG ----------
    table_x = 40
    col_widths = [110, 55, 45, 40, 40, 55]
    headers = ["Subject", "Attempt", "NA", "R", "W", "Marks"]
    row_height = 18

    def draw_row(values, y, bold=False, bg=False):
        x = table_x
        if bg:
            c.setFillGray(0.9)
            c.rect(x, y - row_height + 3, sum(col_widths),
                   row_height, fill=1, stroke=0)
            c.setFillGray(0)

        c.setFont("Helvetica-Bold" if bold else "Helvetica", 10)

        for i, v in enumerate(values):
            c.rect(x, y - row_height + 3, col_widths[i],
                   row_height, stroke=1, fill=0)
            c.drawCentredString(
                x + col_widths[i] / 2, y - 12, str(v)
            )
            x += col_widths[i]

    # ---------- TABLE HEADER ----------
    draw_row(headers, y, bold=True, bg=True)
    y -= row_height

    # ---------- TABLE ROWS ----------
    for sub in result["counted_subjects"] + result["qualifying_subjects"]:
        draw_row(
            [
                sub["name"],
                sub["attempt"],
                sub["na"],
                sub["r"],
                sub["w"],
                sub["marks"]
            ],
            y
        )
        y -= row_height

        if y < 80:
            c.showPage()
            y = height - 50

    y -= 20

    # ---------- FINAL MARKS ----------
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, f"Final Marks: {result['final_marks']}")
    y -= 20

    # ---------- SHIFT RANK ----------
    rank = cand.get("rank", "-")
    total = result.get("total_candidates", "-")

    c.drawString(50, y, f"Shift Rank: {rank} / {total}")

    c.showPage()
    c.save()

    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name=f"{cand['roll']}_result.pdf",
        mimetype="application/pdf"
    )


# ---------------- START ----------------
if __name__ == "__main__":
    app.run()

