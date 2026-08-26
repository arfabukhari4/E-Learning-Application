"""
E-LEARNING PLATFORM - DESKTOP APPLICATION
==========================================
Built with Python + Tkinter, rebuilding the 24-task internship console
script ("Intern_Assignment_Elearning_Platform.ipynb") as a single polished
desktop GUI application, following the same professional coding standards
used in the earlier Calculator project: OOP design, custom exceptions, a
call-logging decorator, JSON persistence, theming, and a strict separation
between business logic and GUI.

Visual theme: "Aurora Twilight" - a deep indigo/violet sidebar with a
teal -> violet -> coral gradient ribbon, crisp white cards with soft drop
shadows and accent stripes, emoji iconography throughout, and a zebra-striped
gradient-accented data grid (see ThemeManager for the full palette).

WHERE EACH ORIGINAL TASK LIVES
--------------------------------
    Task 1  Student Registration        -> Student, StudentRegistry.register, RegistrationPanel (show_register)
    Task 2  Eligibility Checker         -> StudentRegistry.register (UnderageError branch)
    Task 3  Login System                -> AuthService.login, show_login
    Task 4  Course Fee Calculator       -> CourseService.calculate_fee, show_fees
    Task 5  Course Menu                 -> show_courses (course selector + table, replaces while-loop menu)
    Task 6  Student Progress            -> ProgressService.compute, show_progress
    Task 7  Quiz Score                  -> QuizService.compute, show_quiz
    Task 8  Course Management (CRUD)    -> CourseService add/remove/update/search, show_courses
    Task 9  Student Dictionary          -> Student.as_dict, show_students (Treeview)
    Task 10 Attendance System           -> AttendanceService, show_attendance
    Task 11 Tuple Assignment            -> superseded by CertificateService, show_certificate (see PREMIUM FEATURES)
    Task 12 Set Assignment              -> superseded by AnalyticsService, show_analytics (see PREMIUM FEATURES)
    Task 13 Functions                   -> service-layer methods (register/login/calculate_fee/show_courses/progress)
    Task 14 List Comprehension          -> QuizService.above_threshold, shown inside Quiz panel
    Task 15 Dictionary Comprehension    -> CourseService.rows() style filtering, shown inside Courses panel
    Task 16 Nested List (Course detail) -> CourseService.trainers, show_courses table columns
    Task 17 Student ID Generator        -> IDGeneratorService, show_ids
    Task 18 Mini Project (non-OOP)      -> superseded by the OOP service layer + GUI panels below
    Task 19 OOP Introduction            -> User / Student classes
    Task 20 Course Class                -> CourseService (course_name/duration/trainer/fee)
    Task 21 Instructor Class            -> Instructor class
    Task 22 Encapsulation               -> AuthService.__password (private) + getter/setter
    Task 23 Inheritance                 -> User -> Student / Instructor / Admin
    Task 24 Polymorphism                -> dashboard() overridden per role, show_dashboard

PREMIUM FEATURES (beyond the original 24 tasks)
------------------------------------------------
    Certificate Generator   -> CertificateService, show_certificate
    Analytics Dashboard     -> AnalyticsService, show_analytics
    Assignments & Deadlines -> AssignmentService, show_assignments
    Leaderboard             -> LeaderboardService, show_leaderboard
    Discussion Forum        -> ForumService, show_forum
    Study Notes             -> NotesService, show_notes

Run:
    python elearning_desktop_app.py

Requirements:
    Python 3.9+ with the standard 'tkinter' module.
    On Linux, if you see "ModuleNotFoundError: No module named 'tkinter'",
    install it with:  sudo apt install python3-tk
"""

from __future__ import annotations

import json
import re
import time
from datetime import date, datetime, timedelta
from functools import wraps
from pathlib import Path

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog

DATA_FILE = Path("elearning_data.json")


# =============================================================================
# CUSTOM EXCEPTIONS (Task 2, 9 style exception handling)
# =============================================================================
class ELearningError(Exception):
    """Base exception for every application-specific error."""


class RegistrationError(ELearningError):
    """Raised when registration input is invalid."""


class UnderageError(RegistrationError):
    """Raised when a student does not meet the minimum age requirement."""


class InvalidLoginError(ELearningError):
    """Raised when login credentials do not match."""


class CourseNotFoundError(ELearningError):
    """Raised when a referenced course/student does not exist."""


class DuplicateCourseError(ELearningError):
    """Raised when adding a course that already exists."""


class EmptyFieldError(ELearningError):
    """Raised when a required field is left blank."""


# =============================================================================
# DECORATOR - lightweight call logger (mirrors the calculator project)
# =============================================================================
def log_call(func):
    """Logs the name and execution time of the wrapped method to the console."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed_ms = (time.perf_counter() - start) * 1000
        print(f"[LOG] {func.__name__}() took {elapsed_ms:.3f} ms")
        return result

    return wrapper


# =============================================================================
# VALIDATION HELPERS
# =============================================================================
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def require(value, field_name: str) -> str:
    if value is None or str(value).strip() == "":
        raise EmptyFieldError(f"{field_name} cannot be empty.")
    return str(value).strip()


def parse_age(value) -> int:
    try:
        age = int(str(value).strip())
    except (TypeError, ValueError):
        raise RegistrationError("Age must be a whole number.")
    if age <= 0 or age > 120:
        raise RegistrationError("Enter a realistic age.")
    return age


def validate_email(value) -> str:
    value = require(value, "Email")
    if not EMAIL_RE.match(value):
        raise RegistrationError("Enter a valid email address.")
    return value


def parse_int(value, field_name: str) -> int:
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        raise RegistrationError(f"{field_name} must be a whole number.")


def stable_hash(text: str) -> int:
    """Deterministic string hash (no salting), used for certificate IDs and leaderboard scores."""
    h = 0
    for ch in text:
        h = (h * 31 + ord(ch)) & 0xFFFFFFFF
    return h


# =============================================================================
# DOMAIN CLASSES (Task 19 OOP, Task 22 Encapsulation, Task 23 Inheritance,
# Task 24 Polymorphism) - pure logic, no GUI dependency
# =============================================================================
class User:
    """Base user class. dashboard() is overridden polymorphically below."""

    def __init__(self, name: str):
        self.name = name

    def login_message(self) -> str:
        return f"{self.name} logged in successfully."

    def dashboard(self) -> list[str]:
        return ["No dashboard data available."]


class Student(User):
    def __init__(self, name: str, age: int, email: str, course: str, city: str = ""):
        super().__init__(name)
        self.age = age
        self.email = email
        self.course = course
        self.city = city
        self.enrolled_courses: list[str] = [course] if course else []

    def enroll(self, course: str) -> None:
        if course and course not in self.enrolled_courses:
            self.enrolled_courses.append(course)

    def dashboard(self) -> list[str]:
        return [f"Enrolled: {c}" for c in self.enrolled_courses] or ["No enrollments yet."]

    def as_dict(self) -> dict:
        return {"Name": self.name, "Age": self.age, "Email": self.email,
                 "Course": self.course, "City": self.city}


class Instructor(User):
    def __init__(self, name: str, experience: int, technology: str):
        super().__init__(name)
        self.experience = experience
        self.technology = technology
        self.uploaded_courses: list[str] = []

    def upload_course(self, course: str) -> None:
        self.uploaded_courses.append(course)

    def dashboard(self) -> list[str]:
        return [f"Uploaded: {c}" for c in self.uploaded_courses] or ["No uploads yet."]


class Admin(User):
    def remove_student(self, identifier: str, registry: "StudentRegistry") -> None:
        registry.remove_student(identifier)

    def dashboard(self) -> list[str]:
        return ["Manage students and courses from the sidebar."]


# =============================================================================
# SERVICE / LOGIC LAYER - zero tkinter imports, fully unit-testable
# =============================================================================
class StudentRegistry:
    """Holds all registered students (Task 1, 2, 9)."""

    def __init__(self):
        self.students: dict[str, Student] = {}

    @log_call
    def register(self, name, age_raw, email_raw, course, city) -> Student:
        name = require(name, "Name")
        age = parse_age(age_raw)
        email = validate_email(email_raw)
        course = require(course, "Course")
        if age < 18:
            raise UnderageError(f"Must be 18 or older. Wait {18 - age} more year(s).")
        student = Student(name, age, email, course, city.strip() if city else "")
        self.students[email] = student
        return student

    def remove_student(self, identifier: str) -> None:
        for email, s in list(self.students.items()):
            if s.name == identifier or email == identifier:
                del self.students[email]
                return
        raise CourseNotFoundError(f"Student '{identifier}' not found.")

    def all_students(self) -> list[Student]:
        return list(self.students.values())

    def to_json(self) -> list[dict]:
        return [s.as_dict() for s in self.students.values()]

    def load_json(self, rows: list[dict]) -> None:
        for row in rows:
            try:
                s = Student(row["Name"], row["Age"], row["Email"], row["Course"], row.get("City", ""))
                self.students[s.email] = s
            except (KeyError, TypeError):
                continue


class AuthService:
    """Task 3 login + Task 22 encapsulation (private password)."""

    def __init__(self, username: str = "admin", password: str = "python123"):
        self._username = username
        self.__password = password

    def get_username(self) -> str:
        return self._username

    def set_password(self, new_password: str) -> None:
        self.__password = require(new_password, "Password")

    @log_call
    def login(self, username, password) -> str:
        username = require(username, "Username")
        password = require(password, "Password")
        if username == self._username and password == self.__password:
            return "Welcome Admin"
        raise InvalidLoginError("Invalid Credentials")


class CourseService:
    """Task 4, 5, 8, 16, 20 - courses, fees, trainers, duration."""

    def __init__(self):
        self.fees: dict[str, float] = {
            "Python": 8000, "Java": 9000, "Data Analytics": 12000, "AI": 15000,
        }
        self.trainers: dict[str, tuple[str, str]] = {
            "Python": ("Ali", "3 Months"),
            "Java": ("Ahmed", "4 Months"),
            "AI": ("Sara", "6 Months"),
        }

    def course_names(self) -> list[str]:
        return list(self.fees.keys())

    @log_call
    def add_course(self, name, fee, trainer="TBA", duration="TBA") -> None:
        name = require(name, "Course name")
        if name in self.fees:
            raise DuplicateCourseError(f"'{name}' already exists.")
        try:
            fee = float(fee)
        except (TypeError, ValueError):
            raise RegistrationError("Fee must be a number.")
        self.fees[name] = fee
        self.trainers[name] = (trainer or "TBA", duration or "TBA")

    def remove_course(self, name) -> None:
        if name not in self.fees:
            raise CourseNotFoundError(f"'{name}' not found.")
        del self.fees[name]
        self.trainers.pop(name, None)

    def update_course(self, old_name, new_name=None, fee=None) -> None:
        if old_name not in self.fees:
            raise CourseNotFoundError(f"'{old_name}' not found.")
        current_fee = self.fees.pop(old_name)
        trainer_info = self.trainers.pop(old_name, ("TBA", "TBA"))
        final_name = require(new_name, "Course name") if new_name else old_name
        final_fee = float(fee) if fee not in (None, "") else current_fee
        self.fees[final_name] = final_fee
        self.trainers[final_name] = trainer_info

    def search_course(self, name) -> bool:
        return name in self.fees

    @log_call
    def calculate_fee(self, course_name, gender) -> dict:
        if course_name not in self.fees:
            raise CourseNotFoundError(f"'{course_name}' not found.")
        fee = self.fees[course_name]
        if gender.lower() == "female":
            discount = fee * 0.10
            return {"base": fee, "label": "Discount (10%)", "adjustment": discount, "final": fee - discount}
        gst = fee * 0.05
        return {"base": fee, "label": "GST (5%)", "adjustment": gst, "final": fee + gst}

    def rows(self) -> list[tuple]:
        return [(name, self.fees[name], *self.trainers.get(name, ("TBA", "TBA")))
                for name in self.fees]

    def to_json(self) -> dict:
        return {"fees": self.fees, "trainers": self.trainers}

    def load_json(self, data: dict) -> None:
        if data.get("fees"):
            self.fees = {k: float(v) for k, v in data["fees"].items()}
        if data.get("trainers"):
            self.trainers = {k: tuple(v) for k, v in data["trainers"].items()}


class ProgressService:
    @staticmethod
    def compute(completed_raw, total_raw) -> dict:
        completed = parse_int(completed_raw, "Completed modules")
        total = parse_int(total_raw, "Total modules")
        if total <= 0:
            raise RegistrationError("Total modules must be greater than zero.")
        if completed < 0 or completed > total:
            raise RegistrationError("Completed modules must be between 0 and total.")
        percentage = round((completed / total) * 100, 2)
        if percentage >= 80:
            status = "Excellent"
        elif percentage >= 50:
            status = "Good"
        else:
            status = "Keep Learning"
        return {"percentage": percentage, "remaining": total - completed, "status": status}


class QuizService:
    @staticmethod
    def compute(marks: list[int]) -> dict:
        if len(marks) != 5:
            raise RegistrationError("Enter exactly 5 subject marks.")
        total = sum(marks)
        average = round(total / len(marks), 2)
        if average >= 80:
            grade = "A"
        elif average >= 70:
            grade = "B"
        elif average >= 60:
            grade = "C"
        elif average >= 50:
            grade = "D"
        else:
            grade = "F"
        result = "Pass" if average >= 40 else "Fail"
        above_60 = [m for m in marks if m > 60]
        return {"total": total, "average": average, "highest": max(marks), "lowest": min(marks),
                "grade": grade, "result": result, "above_60": above_60}


class AttendanceService:
    def __init__(self):
        self.records: list[str] = ["P", "A", "P", "P", "A", "P"]

    def toggle(self, index: int) -> None:
        self.records[index] = "A" if self.records[index] == "P" else "P"

    def report(self) -> dict:
        present = self.records.count("P")
        absent = self.records.count("A")
        percentage = round((present / len(self.records)) * 100, 2) if self.records else 0.0
        status = "Eligible" if percentage >= 75 else "Short Attendance"
        return {"present": present, "absent": absent, "percentage": percentage, "status": status}


class CertificateService:
    """Bonus - generates a printable-style completion certificate for any registered student."""

    @staticmethod
    def cert_id(email: str, course: str) -> str:
        h = stable_hash(f"{email}|{course}")
        return f"LMN-{h:06X}"[:10]

    @staticmethod
    def build(student: "Student", trainers: dict) -> dict:
        trainer = trainers.get(student.course, ("TBA", "TBA"))[0]
        return {
            "name": student.name,
            "course": student.course,
            "trainer": trainer,
            "date": date.today().strftime("%B %d, %Y"),
            "id": CertificateService.cert_id(student.email, student.course),
        }

    @staticmethod
    def render_text(cert: dict) -> str:
        width = 58
        lines = [
            "=" * width,
            "CERTIFICATE OF COMPLETION".center(width),
            "=" * width,
            "",
            "This certifies that".center(width),
            cert["name"].upper().center(width),
            "has successfully completed the".center(width),
            cert["course"].center(width),
            f"programme, under the guidance of {cert['trainer']}".center(width),
            "",
            f"Date: {cert['date']}".center(width),
            f"Certificate ID: {cert['id']}".center(width),
            "=" * width,
        ]
        return "\n".join(lines)


class AnalyticsService:
    """Bonus - rolls up live figures from every other module into one report."""

    @staticmethod
    def summary(registry: "StudentRegistry", courses: "CourseService", attendance: "AttendanceService") -> dict:
        students = registry.all_students()
        course_names = courses.course_names()
        per_course = [(name, sum(1 for s in students if s.course == name), courses.fees.get(name, 0))
                      for name in course_names]
        per_course.sort(key=lambda row: row[1], reverse=True)
        max_count = max((row[1] for row in per_course), default=0) or 1
        revenue = sum(courses.fees.get(s.course, 0) for s in students)
        att = attendance.report()
        return {
            "total_students": len(students),
            "total_courses": len(course_names),
            "revenue": revenue,
            "attendance_pct": att["percentage"],
            "attendance_status": att["status"],
            "per_course": per_course,
            "max_count": max_count,
        }


class AssignmentService:
    """Bonus - per-course assignments with due dates and overdue detection."""

    def __init__(self):
        today = date.today()
        self.items: list[dict] = [
            {"id": "a1", "title": "Variables & Data Types Worksheet", "course": "Python",
             "due": today + timedelta(days=2), "done": False},
            {"id": "a2", "title": "OOP Mini Project", "course": "Java",
             "due": today - timedelta(days=1), "done": False},
            {"id": "a3", "title": "Linear Regression Notebook", "course": "AI",
             "due": today + timedelta(days=6), "done": False},
        ]
        self._counter = len(self.items)

    @log_call
    def add(self, title, course, due_raw, known_courses: list[str]) -> None:
        title = require(title, "Assignment title")
        course = require(course, "Course")
        if course not in known_courses:
            raise CourseNotFoundError(f"'{course}' is not a known course.")
        due_raw = require(due_raw, "Due date")
        try:
            due = datetime.strptime(due_raw, "%Y-%m-%d").date()
        except ValueError:
            raise RegistrationError("Enter the due date as YYYY-MM-DD.")
        self._counter += 1
        self.items.append({"id": f"a{self._counter}", "title": title, "course": course, "due": due, "done": False})

    def toggle(self, item_id: str) -> None:
        for a in self.items:
            if a["id"] == item_id:
                a["done"] = not a["done"]
                return

    def remove(self, item_id: str) -> None:
        self.items = [a for a in self.items if a["id"] != item_id]

    def all(self) -> list[dict]:
        return sorted(self.items, key=lambda a: a["due"])

    @staticmethod
    def status(a: dict) -> tuple[str, str]:
        if a["done"]:
            return "Done", "success"
        days = (a["due"] - date.today()).days
        if days < 0:
            return f"Overdue by {abs(days)}d", "error"
        if days == 0:
            return "Due today", "warn"
        return f"{days}d left", "ok"

    def to_json(self) -> list[dict]:
        return [{"id": a["id"], "title": a["title"], "course": a["course"],
                 "due": a["due"].isoformat(), "done": a["done"]} for a in self.items]

    def load_json(self, rows: list[dict]) -> None:
        loaded = []
        for row in rows:
            try:
                due = datetime.strptime(row["due"], "%Y-%m-%d").date()
                loaded.append({"id": row["id"], "title": row["title"], "course": row["course"],
                               "due": due, "done": bool(row.get("done", False))})
            except (KeyError, ValueError):
                continue
        if loaded:
            self.items = loaded
            self._counter = len(loaded)


class LeaderboardService:
    """Bonus - deterministic engagement scoring & badge tiers across registered students."""

    @staticmethod
    def score_of(student: "Student") -> int:
        h = stable_hash(f"{student.email}|{student.name}")
        return 500 + (h % 480)

    @staticmethod
    def badge(score: int) -> str:
        if score >= 850:
            return "Gold"
        if score >= 680:
            return "Silver"
        return "Bronze"

    @staticmethod
    def rows(registry: "StudentRegistry") -> list[tuple]:
        scored = [(s, LeaderboardService.score_of(s)) for s in registry.all_students()]
        scored.sort(key=lambda pair: pair[1], reverse=True)
        return [(s.name, s.course, score, LeaderboardService.badge(score)) for s, score in scored]


class ForumService:
    """Bonus - course-scoped Q&A threads with upvotes and replies."""

    def __init__(self):
        self.threads: list[dict] = [
            {"id": "t1", "course": "Python", "author": "Rahul",
             "question": "Why does my list index throw an error after removing an item mid-loop?",
             "votes": 4, "replies": [("Ali (Trainer)",
                                       "You're mutating the list while iterating - loop over a copy "
                                       "with list(items) or use a while loop instead.")]},
            {"id": "t2", "course": "AI", "author": "Sara K.",
             "question": "What's a good learning rate to start with for a simple linear regression from scratch?",
             "votes": 2, "replies": []},
        ]
        self._counter = len(self.threads)

    def ask(self, course, author, question, known_courses: list[str]) -> None:
        course = require(course, "Course")
        if course not in known_courses:
            raise CourseNotFoundError(f"'{course}' is not a known course.")
        author = require(author, "Your name")
        question = require(question, "Question")
        self._counter += 1
        self.threads.insert(0, {"id": f"t{self._counter}", "course": course, "author": author,
                                 "question": question, "votes": 0, "replies": []})

    def reply(self, thread_id, author, text) -> None:
        thread = next((t for t in self.threads if t["id"] == thread_id), None)
        if not thread:
            raise CourseNotFoundError("Thread not found.")
        author = require(author, "Your name")
        text = require(text, "Reply")
        thread["replies"].append((author, text))

    def upvote(self, thread_id) -> None:
        for t in self.threads:
            if t["id"] == thread_id:
                t["votes"] += 1
                return

    def by_course(self, course) -> list[dict]:
        return sorted([t for t in self.threads if t["course"] == course], key=lambda t: t["votes"], reverse=True)

    def to_json(self) -> list[dict]:
        return [{"id": t["id"], "course": t["course"], "author": t["author"], "question": t["question"],
                 "votes": t["votes"], "replies": [list(r) for r in t["replies"]]} for t in self.threads]

    def load_json(self, rows: list[dict]) -> None:
        loaded = []
        for row in rows:
            try:
                loaded.append({"id": row["id"], "course": row["course"], "author": row["author"],
                               "question": row["question"], "votes": int(row.get("votes", 0)),
                               "replies": [tuple(r) for r in row.get("replies", [])]})
            except (KeyError, TypeError):
                continue
        if loaded:
            self.threads = loaded
            self._counter = len(loaded)


class NotesService:
    """Bonus - a per-course study-notes library with pin and search."""

    def __init__(self):
        self.items: list[dict] = [
            {"id": "n1", "course": "Java", "title": "OOP Cheat Sheet",
             "body": "Encapsulation, Inheritance, Polymorphism, Abstraction - remember EIPA. "
                     "Constructors run top-down through the inheritance chain.", "pinned": True},
        ]
        self._counter = len(self.items)

    def add(self, course, title, body, known_courses: list[str]) -> None:
        course = require(course, "Course")
        if course not in known_courses:
            raise CourseNotFoundError(f"'{course}' is not a known course.")
        title = require(title, "Title")
        body = require(body, "Note content")
        self._counter += 1
        self.items.insert(0, {"id": f"n{self._counter}", "course": course, "title": title,
                              "body": body, "pinned": False})

    def remove(self, note_id) -> None:
        self.items = [n for n in self.items if n["id"] != note_id]

    def toggle_pin(self, note_id) -> None:
        for n in self.items:
            if n["id"] == note_id:
                n["pinned"] = not n["pinned"]
                return

    def search(self, query: str, course: str) -> list[dict]:
        q = (query or "").strip().lower()
        rows = [n for n in self.items if course in (None, "All") or n["course"] == course]
        if q:
            rows = [n for n in rows if q in n["title"].lower() or q in n["body"].lower()]
        return sorted(rows, key=lambda n: n["pinned"], reverse=True)

    def to_json(self) -> list[dict]:
        return [dict(n) for n in self.items]

    def load_json(self, rows: list[dict]) -> None:
        loaded = []
        for row in rows:
            try:
                loaded.append({"id": row["id"], "course": row["course"], "title": row["title"],
                               "body": row["body"], "pinned": bool(row.get("pinned", False))})
            except (KeyError, TypeError):
                continue
        if loaded:
            self.items = loaded
            self._counter = len(loaded)


class IDGeneratorService:
    @staticmethod
    def generate(start_id_raw, count_raw) -> list[str]:
        start_id = parse_int(start_id_raw, "Start ID")
        count = parse_int(count_raw, "Count")
        if count <= 0 or count > 500:
            raise RegistrationError("Enter a count between 1 and 500.")
        return [f"ST{start_id + i}" for i in range(count)]


class PersistenceManager:
    """JSON persistence, mirroring HistoryManager.save()/_load() (Task 15/16)."""

    def __init__(self, path: Path = DATA_FILE):
        self.path = path

    def load(self) -> dict:
        if self.path.exists():
            try:
                return json.loads(self.path.read_text())
            except json.JSONDecodeError:
                return {}
        return {}

    @log_call
    def save(self, data: dict) -> None:
        self.path.write_text(json.dumps(data, indent=2))


# =============================================================================
# THEME MANAGER - "Aurora Twilight" palette: deep indigo/violet sidebar with a
# teal -> violet -> coral gradient, crisp white cards, and vivid accent pops.
# =============================================================================
class ThemeManager:
    THEME = {
        "bg": "#F5F2FC",              # soft lavender-white canvas
        "sidebar_bg": "#241B3A",      # deep indigo (gradient top)
        "sidebar_bg2": "#3B2160",     # violet plum (gradient bottom)
        "sidebar_fg": "#F1E9FF",
        "sidebar_muted": "#B7A6E0",
        "sidebar_active": "#6F42E8",  # vivid violet highlight
        "display_bg": "#FFFFFF",
        "display_fg": "#241B3A",
        "button_bg": "#FF6F5E",       # coral
        "button_fg": "#FFFFFF",
        "accent_bg": "#00BFA6",       # teal
        "accent2": "#FF9F45",         # amber (secondary accent for gradients)
        "operator_bg": "#6F42E8",     # primary violet action
        "operator_fg": "#FFFFFF",
        "error_fg": "#E5484D",
        "success_fg": "#12B76A",
        "border": "#E4DCF7",
        "shadow": "#DCD3F2",
        "muted_fg": "#7A6FA0",
    }

    # gradient bands used for the sidebar edge ribbon / header underline
    GRADIENT = ["#00BFA6", "#6F42E8", "#FF6F5E"]

    # emoji glyphs paired with each sidebar nav label
    NAV_ICONS = {
        "Register": "📝", "Login": "🔐", "Course Fees": "💳", "Courses": "📚",
        "Progress": "📈", "Quiz Score": "🧠", "Attendance": "🗓️", "Students": "👩‍🎓",
        "Certificates": "🏅", "Analytics": "📊", "Assignments": "🗂️",
        "Leaderboard": "🏆", "Forum": "💬", "Study Notes": "🗒️",
        "Student IDs": "🔢", "Dashboard": "🧭",
    }

    # emoji glyph shown beside each panel's big header title
    PANEL_ICONS = {
        "Student Registration": "📝", "Login System": "🔐", "Course Fee Calculator": "💳",
        "Course Management": "📚", "Student Progress": "📈", "Quiz Score": "🧠",
        "Attendance System": "🗓️", "Registered Students": "👩‍🎓",
        "Certificate Generator": "🏅", "Analytics Dashboard": "📊",
        "Assignments & Deadlines": "🗂️", "Leaderboard": "🏆", "Discussion Forum": "💬",
        "Study Notes": "🗒️", "Student ID Generator": "🔢", "Role Dashboard": "🧭",
    }

    @property
    def colors(self) -> dict:
        return self.THEME

    @staticmethod
    def blend(hex1: str, hex2: str, t: float) -> str:
        """Linear-interpolate between two '#RRGGBB' colors at t in [0, 1]."""
        r1, g1, b1 = int(hex1[1:3], 16), int(hex1[3:5], 16), int(hex1[5:7], 16)
        r2, g2, b2 = int(hex2[1:3], 16), int(hex2[3:5], 16), int(hex2[5:7], 16)
        r = round(r1 + (r2 - r1) * t)
        g = round(g1 + (g2 - g1) * t)
        b = round(b1 + (b2 - b1) * t)
        return f"#{r:02X}{g:02X}{b:02X}"

    @classmethod
    def paint_vertical_gradient(cls, canvas: tk.Canvas, width: int, height: int,
                                 stops: list[str]) -> None:
        """Fill a Canvas with a smooth multi-stop vertical gradient."""
        canvas.delete("gradient")
        if height <= 0:
            return
        segments = max(len(stops) - 1, 1)
        for y in range(height):
            t = y / max(height - 1, 1)
            pos = t * segments
            i = min(int(pos), segments - 1)
            local_t = pos - i
            color = cls.blend(stops[i], stops[i + 1], local_t)
            canvas.create_line(0, y, width, y, fill=color, tags="gradient")
        canvas.tag_lower("gradient")


# =============================================================================
# MAIN APPLICATION - GUI (sidebar navigation + swappable content panel)
# =============================================================================
class ELearningApp:
    WIDTH = 1040
    HEIGHT = 660

    def __init__(self, root: tk.Tk):
        self.root = root
        self.theme = ThemeManager()
        self.c = self.theme.colors

        self.persistence = PersistenceManager()
        self.registry = StudentRegistry()
        self.auth = AuthService()
        self.courses = CourseService()
        self.attendance = AttendanceService()
        self.assignments = AssignmentService()
        self.forum = ForumService()
        self.notes = NotesService()

        self._load_saved_data()

        self.buttons: list[tk.Button] = []
        self.nav_buttons: dict[str, tuple[tk.Button, tk.Frame]] = {}

        self._configure_window()
        self.create_gui()
        self.show_register()

    # ------------------------------------------------------------ Startup
    def _load_saved_data(self) -> None:
        data = self.persistence.load()
        if data.get("students"):
            self.registry.load_json(data["students"])
        if data.get("courses"):
            self.courses.load_json(data["courses"])
        if data.get("assignments"):
            self.assignments.load_json(data["assignments"])
        if data.get("forum"):
            self.forum.load_json(data["forum"])
        if data.get("notes"):
            self.notes.load_json(data["notes"])

    # ------------------------------------------------------------ Window
    def _configure_window(self) -> None:
        self.root.title("E-Learning Platform")
        self.root.configure(bg=self.c["bg"])
        self.root.minsize(self.WIDTH, self.HEIGHT)
        self._center_window()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _center_window(self) -> None:
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (self.WIDTH // 2)
        y = (self.root.winfo_screenheight() // 2) - (self.HEIGHT // 2)
        self.root.geometry(f"{self.WIDTH}x{self.HEIGHT}+{x}+{y}")

    # ---------------------------------------------------------- GUI build
    def create_gui(self) -> None:
        self._build_sidebar()
        self.content = tk.Frame(self.root, bg=self.c["bg"])
        self.content.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=24, pady=20)

    def _build_sidebar(self) -> None:
        outer = tk.Frame(self.root, bg=self.c["sidebar_bg"])
        outer.pack(side=tk.LEFT, fill=tk.Y)

        sidebar = tk.Frame(outer, bg=self.c["sidebar_bg"], width=222)
        sidebar.pack(side=tk.LEFT, fill=tk.Y)
        sidebar.pack_propagate(False)

        # slim rainbow gradient ribbon that separates sidebar from content
        ribbon = tk.Canvas(outer, width=5, highlightthickness=0, bd=0)
        ribbon.pack(side=tk.LEFT, fill=tk.Y)

        def paint_ribbon(event=None):
            h = max(ribbon.winfo_height(), self.HEIGHT)
            self.theme.paint_vertical_gradient(ribbon, 5, h, self.theme.GRADIENT)

        ribbon.bind("<Configure>", paint_ribbon)

        # gradient header banner (logo block) drawn on a Canvas
        header = tk.Canvas(sidebar, width=222, height=104, highlightthickness=0, bd=0)
        header.pack(fill=tk.X)

        def paint_header(event=None):
            self.theme.paint_vertical_gradient(header, 222, 104,
                                                [self.c["sidebar_bg"], self.c["sidebar_bg2"]])
            header.create_text(20, 40, anchor="w", text="\U0001F393", font=("Segoe UI Emoji", 22))
            header.create_text(56, 32, anchor="w", text="E-Learning", font=("Segoe UI", 16, "bold"),
                                fill=self.c["sidebar_fg"])
            header.create_text(56, 54, anchor="w", text="Aurora Studio", font=("Segoe UI", 9, "italic"),
                                fill=self.c["sidebar_muted"])
            for i, color in enumerate(self.theme.GRADIENT):
                header.create_oval(20 + i * 16, 76, 30 + i * 16, 86, fill=color, outline="")

        paint_header()

        nav_items = [
            ("Register", self.show_register),
            ("Login", self.show_login),
            ("Course Fees", self.show_fees),
            ("Courses", self.show_courses),
            ("Progress", self.show_progress),
            ("Quiz Score", self.show_quiz),
            ("Attendance", self.show_attendance),
            ("Students", self.show_students),
            ("Certificates", self.show_certificate),
            ("Analytics", self.show_analytics),
            ("Assignments", self.show_assignments),
            ("Leaderboard", self.show_leaderboard),
            ("Forum", self.show_forum),
            ("Study Notes", self.show_notes),
            ("Student IDs", self.show_ids),
            ("Dashboard", self.show_dashboard),
        ]
        nav_scroll = tk.Frame(sidebar, bg=self.c["sidebar_bg"])
        nav_scroll.pack(fill=tk.BOTH, expand=True, pady=(6, 0))
        for label, command in nav_items:
            self._add_nav_button(nav_scroll, label, command)

        exit_btn = tk.Button(sidebar, text="\U0001F4BE  Save & Exit", font=("Segoe UI", 11, "bold"),
                              bd=0, relief="flat", bg=self.c["button_bg"], fg=self.c["button_fg"],
                              activebackground=self.c["accent2"], activeforeground=self.c["button_fg"],
                              cursor="hand2", command=self._on_close)
        exit_btn.pack(fill=tk.X, side=tk.BOTTOM, padx=14, pady=16, ipady=11)
        self._bind_hover(exit_btn, self.c["button_bg"], hover_bg=self.c["accent2"])

    def _add_nav_button(self, parent, label: str, command) -> None:
        row = tk.Frame(parent, bg=self.c["sidebar_bg"])
        row.pack(fill=tk.X, padx=10, pady=2)

        indicator = tk.Frame(row, bg=self.c["sidebar_bg"], width=4)
        indicator.pack(side=tk.LEFT, fill=tk.Y)

        icon = self.theme.NAV_ICONS.get(label, "\u2022")
        btn = tk.Button(row, text=f"  {icon}   {label}", font=("Segoe UI", 11), bd=0, relief="flat",
                         anchor="w", padx=8, bg=self.c["sidebar_bg"], fg=self.c["sidebar_fg"],
                         activebackground=self.c["sidebar_active"], activeforeground="#FFFFFF",
                         cursor="hand2", command=lambda: self._navigate(label, command))
        btn.pack(fill=tk.X, ipady=9)
        self._bind_hover(btn, self.c["sidebar_bg"], hover_bg=self.c["sidebar_active"])
        self.nav_buttons[label] = (btn, indicator)

    def _navigate(self, label: str, command) -> None:
        for name, (btn, indicator) in self.nav_buttons.items():
            active = name == label
            btn.configure(bg=self.c["sidebar_active"] if active else self.c["sidebar_bg"],
                          font=("Segoe UI", 11, "bold" if active else "normal"))
            indicator.configure(bg=self.c["accent2"] if active else self.c["sidebar_bg"])
        command()

    # -------------------------------------------------------------- Hover
    def _bind_hover(self, widget, normal_bg: str, hover_bg: str | None = None) -> None:
        hover_bg = hover_bg or self.c["accent_bg"]
        widget.bind("<Enter>", lambda e: widget.configure(bg=hover_bg, cursor="hand2"))
        widget.bind("<Leave>", lambda e: widget.configure(bg=normal_bg))

    # ------------------------------------------------------- Panel helpers
    def _clear_content(self) -> None:
        for widget in self.content.winfo_children():
            widget.destroy()

    def _panel_header(self, text: str, subtitle: str = "") -> None:
        icon = self.theme.PANEL_ICONS.get(text, "\u2728")
        title_row = tk.Frame(self.content, bg=self.c["bg"])
        title_row.pack(fill=tk.X, anchor="w")
        tk.Label(title_row, text=icon, font=("Segoe UI Emoji", 20),
                 bg=self.c["bg"], fg=self.c["display_fg"]).pack(side=tk.LEFT, padx=(0, 8))
        tk.Label(title_row, text=text, font=("Segoe UI", 19, "bold"),
                 bg=self.c["bg"], fg=self.c["display_fg"]).pack(side=tk.LEFT, anchor="w")
        if subtitle:
            tk.Label(self.content, text=subtitle, font=("Segoe UI", 10),
                     bg=self.c["bg"], fg=self.c["muted_fg"]).pack(anchor="w", pady=(2, 8))
        # a tiny three-color gradient underline for a bit of visual flair
        underline = tk.Canvas(self.content, height=4, highlightthickness=0, bd=0)
        underline.pack(fill=tk.X, pady=(0, 14))
        underline.update_idletasks()

        def paint(event=None):
            width = underline.winfo_width() or 640
            underline.delete("grad")
            segs = len(self.theme.GRADIENT) - 1
            for x in range(width):
                t = x / max(width - 1, 1)
                pos = t * segs
                i = min(int(pos), segs - 1)
                color = self.theme.blend(self.theme.GRADIENT[i], self.theme.GRADIENT[i + 1], pos - i)
                underline.create_line(x, 0, x, 4, fill=color, tags="grad")

        underline.bind("<Configure>", paint)

    def _card(self) -> tk.Frame:
        wrapper = tk.Frame(self.content, bg=self.c["bg"])
        wrapper.pack(fill=tk.X, anchor="n", pady=(0, 4))

        # soft "shadow" plate peeking out behind the card for a lifted, modern feel
        shadow = tk.Frame(wrapper, bg=self.c["shadow"])
        shadow.place(x=5, y=5, relwidth=1, relheight=1)

        stripe = tk.Frame(wrapper, bg=self.c["accent_bg"], height=4)
        card_holder = tk.Frame(wrapper, bg=self.c["display_bg"],
                                highlightbackground=self.c["border"], highlightthickness=1)
        stripe.pack(fill=tk.X)
        card_holder.pack(fill=tk.X)

        card = tk.Frame(card_holder, bg=self.c["display_bg"], padx=22, pady=18)
        card.pack(fill=tk.X)
        return card

    def _labeled_entry(self, parent, label_text: str, show: str | None = None) -> tk.StringVar:
        row = tk.Frame(parent, bg=self.c["display_bg"])
        row.pack(fill=tk.X, pady=6)
        tk.Label(row, text=label_text, width=16, anchor="w", bg=self.c["display_bg"],
                  fg=self.c["muted_fg"], font=("Segoe UI", 10, "bold")).pack(side=tk.LEFT)
        var = tk.StringVar()
        entry = tk.Entry(row, textvariable=var, font=("Segoe UI", 11), bd=1, relief="solid",
                          show=show or "", highlightthickness=2,
                          highlightbackground=self.c["border"], highlightcolor=self.c["accent_bg"])
        entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=5)
        return var, entry

    def _labeled_combo(self, parent, label_text: str, values: list[str]) -> tk.StringVar:
        row = tk.Frame(parent, bg=self.c["display_bg"])
        row.pack(fill=tk.X, pady=6)
        tk.Label(row, text=label_text, width=16, anchor="w", bg=self.c["display_bg"],
                  fg=self.c["muted_fg"], font=("Segoe UI", 10, "bold")).pack(side=tk.LEFT)
        var = tk.StringVar(value=values[0] if values else "")
        style = ttk.Style()
        style.configure("Aurora.TCombobox", fieldbackground=self.c["display_bg"],
                        background=self.c["display_bg"], foreground=self.c["display_fg"],
                        arrowcolor=self.c["operator_bg"], bordercolor=self.c["border"])
        combo = ttk.Combobox(row, textvariable=var, values=values, state="readonly",
                              font=("Segoe UI", 10), style="Aurora.TCombobox")
        combo.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=3)
        return var, combo

    def _action_button(self, parent, text: str, command, primary: bool = True) -> tk.Button:
        bg = self.c["operator_bg"] if primary else self.c["button_bg"]
        fg = self.c["operator_fg"] if primary else self.c["button_fg"]
        hover = self.c["accent_bg"] if primary else self.c["accent2"]
        glyph = "\u2192 " if primary else "\u21BB "
        btn = tk.Button(parent, text=f"{glyph}{text}", command=command, bg=bg, fg=fg,
                         font=("Segoe UI", 11, "bold"), bd=0, relief="flat", cursor="hand2")
        btn.pack(pady=(14, 0), ipady=10, fill=tk.X)
        self._bind_hover(btn, bg, hover_bg=hover)
        self.buttons.append(btn)
        return btn

    def _banner(self, parent, message: str, success: bool = True) -> None:
        color = self.c["success_fg"] if success else self.c["error_fg"]
        icon = "\u2705" if success else "\u26A0\uFE0F"
        row = tk.Frame(parent, bg=self.c["display_bg"])
        row.pack(fill=tk.X, pady=(12, 0), anchor="w")
        tk.Label(row, text=icon, bg=self.c["display_bg"], font=("Segoe UI Emoji", 11)).pack(side=tk.LEFT, padx=(0, 6))
        tk.Label(row, text=message, fg=color, bg=self.c["display_bg"],
                 font=("Segoe UI", 10, "bold"), wraplength=500, justify="left").pack(side=tk.LEFT, anchor="w")

    def _styled_treeview(self, parent, columns: list[str]) -> ttk.Treeview:
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Aurora.Treeview", background=self.c["display_bg"], fieldbackground=self.c["display_bg"],
                         foreground=self.c["display_fg"], rowheight=30, font=("Segoe UI", 10), borderwidth=0)
        style.configure("Aurora.Treeview.Heading", background=self.c["sidebar_bg2"], foreground=self.c["sidebar_fg"],
                         font=("Segoe UI", 10, "bold"), relief="flat", padding=(8, 8))
        style.map("Aurora.Treeview.Heading", background=[("active", self.c["sidebar_active"])])
        style.map("Aurora.Treeview", background=[("selected", self.c["operator_bg"])],
                  foreground=[("selected", "#FFFFFF")])

        holder = tk.Frame(parent, bg=self.c["border"], padx=1, pady=1)
        holder.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        tree = ttk.Treeview(holder, columns=columns, show="headings", style="Aurora.Treeview", height=10)
        tree.tag_configure("odd", background=self.c["bg"])
        tree.tag_configure("even", background=self.c["display_bg"])
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, anchor="w", width=140)
        tree.pack(fill=tk.BOTH, expand=True)

        original_insert = tree.insert

        def zebra_insert(parent_="", index=tk.END, **kwargs):
            iid = original_insert(parent_, index, **kwargs)
            row_num = len(tree.get_children())
            tree.item(iid, tags=("even" if row_num % 2 == 0 else "odd",))
            return iid

        tree.insert = zebra_insert
        return tree

    # ============================================================ PANELS
    # ------------------------------------------------------- Register
    def show_register(self) -> None:
        self._clear_content()
        self._panel_header("Student Registration", "Task 1 & 2 - registration with eligibility check")
        card = self._card()

        name_var, name_entry = self._labeled_entry(card, "Name")
        age_var, age_entry = self._labeled_entry(card, "Age")
        email_var, _ = self._labeled_entry(card, "Email")
        course_var, _ = self._labeled_combo(card, "Course", self.courses.course_names())
        city_var, city_entry = self._labeled_entry(card, "City")

        def submit(event=None):
            try:
                student = self.registry.register(name_var.get(), age_var.get(), email_var.get(),
                                                   course_var.get(), city_var.get())
                self._banner(card, f"Registration Successful - Welcome, {student.name}!", success=True)
                for var in (name_var, age_var, email_var, city_var):
                    var.set("")
            except ELearningError as exc:
                self._banner(card, str(exc), success=False)

        city_entry.bind("<Return>", submit)
        self._action_button(card, "Register Student", submit)

    # ------------------------------------------------------- Login
    def show_login(self) -> None:
        self._clear_content()
        self._panel_header("Login System", "Task 3 - admin authentication")
        card = self._card()

        user_var, _ = self._labeled_entry(card, "Username")
        pass_var, pass_entry = self._labeled_entry(card, "Password", show="*")

        def submit(event=None):
            try:
                message = self.auth.login(user_var.get(), pass_var.get())
                self._banner(card, message, success=True)
            except ELearningError as exc:
                self._banner(card, str(exc), success=False)

        pass_entry.bind("<Return>", submit)
        self._action_button(card, "Login", submit)

    # ------------------------------------------------------- Fees
    def show_fees(self) -> None:
        self._clear_content()
        self._panel_header("Course Fee Calculator", "Task 4 - fee, discount, and GST")
        card = self._card()

        course_var, _ = self._labeled_combo(card, "Course", self.courses.course_names())
        gender_var, _ = self._labeled_combo(card, "Gender", ["Female", "Male"])

        result_label = tk.Label(card, text="", bg=self.c["display_bg"], fg=self.c["display_fg"],
                                 font=("Consolas", 11), justify="left")

        def submit():
            try:
                res = self.courses.calculate_fee(course_var.get(), gender_var.get())
                text = (f"Base Fee        : {res['base']:.2f}\n"
                        f"{res['label']:<16} : {res['adjustment']:.2f}\n"
                        f"Final Fee        : {res['final']:.2f}")
                result_label.configure(text=text, fg=self.c["display_fg"])
                result_label.pack(anchor="w", pady=(14, 0))
            except ELearningError as exc:
                self._banner(card, str(exc), success=False)

        self._action_button(card, "Calculate Fee", submit)

    # ------------------------------------------------------- Courses (CRUD)
    def show_courses(self) -> None:
        self._clear_content()
        self._panel_header("Course Management", "Task 5, 8, 16, 20 - view, add, update, remove, search")

        toolbar = tk.Frame(self.content, bg=self.c["bg"])
        toolbar.pack(fill=tk.X)

        tree = self._styled_treeview(self.content, ["Course", "Fee", "Trainer", "Duration"])

        def refresh():
            tree.delete(*tree.get_children())
            for row in self.courses.rows():
                tree.insert("", tk.END, values=row)

        def add_course():
            name = simpledialog.askstring("Add Course", "Course name:", parent=self.root)
            if not name:
                return
            fee = simpledialog.askstring("Add Course", "Course fee:", parent=self.root)
            trainer = simpledialog.askstring("Add Course", "Trainer name (optional):", parent=self.root) or "TBA"
            duration = simpledialog.askstring("Add Course", "Duration (optional):", parent=self.root) or "TBA"
            try:
                self.courses.add_course(name, fee, trainer, duration)
                refresh()
            except ELearningError as exc:
                messagebox.showerror("Course Error", str(exc))

        def update_course():
            selection = tree.selection()
            if not selection:
                messagebox.showinfo("Update Course", "Select a course row first.")
                return
            old_name = tree.item(selection[0], "values")[0]
            new_name = simpledialog.askstring("Update Course", "New course name (blank to keep):", parent=self.root)
            new_fee = simpledialog.askstring("Update Course", "New fee (blank to keep):", parent=self.root)
            try:
                self.courses.update_course(old_name, new_name or None, new_fee or None)
                refresh()
            except ELearningError as exc:
                messagebox.showerror("Course Error", str(exc))

        def remove_course():
            selection = tree.selection()
            if not selection:
                messagebox.showinfo("Remove Course", "Select a course row first.")
                return
            name = tree.item(selection[0], "values")[0]
            try:
                self.courses.remove_course(name)
                refresh()
            except ELearningError as exc:
                messagebox.showerror("Course Error", str(exc))

        def search_course():
            name = simpledialog.askstring("Search Course", "Course name:", parent=self.root)
            if not name:
                return
            found = self.courses.search_course(name)
            messagebox.showinfo("Search Course", f"'{name}' {'was found.' if found else 'was not found.'}")

        for label, cmd in [("+ Add", add_course), ("Update", update_course),
                            ("Remove", remove_course), ("Search", search_course), ("Refresh", refresh)]:
            btn = tk.Button(toolbar, text=label, command=cmd, bg=self.c["operator_bg"], fg=self.c["operator_fg"],
                             font=("Segoe UI", 10, "bold"), bd=0, relief="flat")
            btn.pack(side=tk.LEFT, padx=(0, 8), ipady=6, ipadx=10)
            self._bind_hover(btn, self.c["operator_bg"])

        refresh()

    # ------------------------------------------------------- Progress
    def show_progress(self) -> None:
        self._clear_content()
        self._panel_header("Student Progress", "Task 6 - module completion tracker")
        card = self._card()

        completed_var, _ = self._labeled_entry(card, "Completed Modules")
        total_var, total_entry = self._labeled_entry(card, "Total Modules")
        completed_var.set("7")
        total_var.set("10")

        bar = ttk.Progressbar(card, orient="horizontal", length=300, mode="determinate")
        status_label = tk.Label(card, text="", bg=self.c["display_bg"], fg=self.c["display_fg"],
                                 font=("Segoe UI", 11, "bold"))

        def submit(event=None):
            try:
                res = ProgressService.compute(completed_var.get(), total_var.get())
                bar["value"] = res["percentage"]
                bar.pack(pady=(16, 6), fill=tk.X)
                status_label.configure(
                    text=f"Progress: {res['percentage']}%  |  Remaining: {res['remaining']}  |  Status: {res['status']}")
                status_label.pack(anchor="w")
            except ELearningError as exc:
                self._banner(card, str(exc), success=False)

        total_entry.bind("<Return>", submit)
        self._action_button(card, "Calculate Progress", submit)

    # ------------------------------------------------------- Quiz
    def show_quiz(self) -> None:
        self._clear_content()
        self._panel_header("Quiz Score", "Task 7 & 14 - totals, average, grade, marks above 60")
        card = self._card()

        mark_vars = []
        for i in range(5):
            var, _ = self._labeled_entry(card, f"Subject {i + 1} Marks")
            mark_vars.append(var)

        result_label = tk.Label(card, text="", bg=self.c["display_bg"], fg=self.c["display_fg"],
                                 font=("Consolas", 10), justify="left")

        def submit():
            try:
                marks = [parse_int(v.get(), f"Subject {i + 1}") for i, v in enumerate(mark_vars)]
                res = QuizService.compute(marks)
                text = (f"Total   : {res['total']}\nAverage : {res['average']}\n"
                        f"Highest : {res['highest']}\nLowest  : {res['lowest']}\n"
                        f"Grade   : {res['grade']}\nResult  : {res['result']}\n"
                        f"Marks > 60 : {res['above_60']}")
                result_label.configure(text=text)
                result_label.pack(anchor="w", pady=(14, 0))
            except ELearningError as exc:
                self._banner(card, str(exc), success=False)

        self._action_button(card, "Compute Result", submit)

    # ------------------------------------------------------- Attendance
    def show_attendance(self) -> None:
        self._clear_content()
        self._panel_header("Attendance System", "Task 10 - toggle each day, live percentage")
        card = self._card()

        days_frame = tk.Frame(card, bg=self.c["display_bg"])
        days_frame.pack(fill=tk.X)

        summary_label = tk.Label(card, text="", bg=self.c["display_bg"], fg=self.c["display_fg"],
                                  font=("Segoe UI", 11, "bold"))
        summary_label.pack(anchor="w", pady=(14, 0))

        def refresh_summary():
            res = self.attendance.report()
            summary_label.configure(
                text=f"Present: {res['present']}  |  Absent: {res['absent']}  |  "
                     f"{res['percentage']}%  |  Status: {res['status']}")

        def toggle(i, btn):
            self.attendance.toggle(i)
            record = self.attendance.records[i]
            btn.configure(text=f"Day {i + 1}: {record}",
                          bg=self.c["success_fg"] if record == "P" else self.c["error_fg"])
            refresh_summary()

        for i, record in enumerate(self.attendance.records):
            btn = tk.Button(days_frame, text=f"Day {i + 1}: {record}",
                             bg=self.c["success_fg"] if record == "P" else self.c["error_fg"],
                             fg="#FFFFFF", font=("Segoe UI", 10, "bold"), bd=0, relief="flat")
            btn.configure(command=lambda i=i, b=None: None)
            btn.pack(side=tk.LEFT, padx=4, ipadx=8, ipady=8)
            btn.configure(command=lambda i=i, b=btn: toggle(i, b))

        refresh_summary()

    # ------------------------------------------------------- Students
    def show_students(self) -> None:
        self._clear_content()
        self._panel_header("Registered Students", "Task 9 - student dictionary view")

        toolbar = tk.Frame(self.content, bg=self.c["bg"])
        toolbar.pack(fill=tk.X, pady=(0, 10))
        remove_var = tk.StringVar()
        remove_entry = tk.Entry(toolbar, textvariable=remove_var, font=("Segoe UI", 10),
                                 bd=1, relief="solid", width=30)
        remove_entry.pack(side=tk.LEFT, ipady=5, padx=(0, 8))
        remove_btn = tk.Button(toolbar, text="Remove by Name/Email", bg=self.c["operator_bg"],
                                fg=self.c["operator_fg"], font=("Segoe UI", 10, "bold"), bd=0, relief="flat")
        remove_btn.pack(side=tk.LEFT, ipady=6, ipadx=10)
        self._bind_hover(remove_btn, self.c["operator_bg"])

        tree = self._styled_treeview(self.content, ["Name", "Age", "Email", "Course", "City"])
        empty_label = tk.Label(self.content, text="No students registered yet.", bg=self.c["bg"],
                                fg=self.c["accent_bg"], font=("Segoe UI", 10, "italic"))

        def refresh():
            tree.delete(*tree.get_children())
            students = self.registry.all_students()
            for s in students:
                d = s.as_dict()
                tree.insert("", tk.END, values=(d["Name"], d["Age"], d["Email"], d["Course"], d["City"]))
            if students:
                empty_label.pack_forget()
            else:
                empty_label.pack(anchor="w", pady=(10, 0))

        def remove_student():
            try:
                self.registry.remove_student(require(remove_var.get(), "Student"))
                remove_var.set("")
                refresh()
            except ELearningError as exc:
                messagebox.showerror("Remove Student", str(exc))

        remove_btn.configure(command=remove_student)
        remove_entry.bind("<Return>", lambda e: remove_student())
        refresh()

    # ------------------------------------------------------- Certificates
    def show_certificate(self) -> None:
        self._clear_content()
        self._panel_header("Certificate Generator", "Bonus - issue a completion certificate for any registered student")
        card = self._card()

        students = self.registry.all_students()
        if not students:
            tk.Label(card, text="Register a student first - certificates are generated from live enrollment records.",
                     bg=self.c["display_bg"], fg=self.c["error_fg"], font=("Segoe UI", 10, "bold"),
                     wraplength=520, justify="left").pack(anchor="w")
            return

        options = [f"{s.name} — {s.course} ({s.email})" for s in students]
        student_var, _ = self._labeled_combo(card, "Student", options)

        cert_box = tk.Text(card, font=("Consolas", 10), height=13, bd=1, relief="solid",
                            bg=self.c["bg"], fg=self.c["display_fg"], wrap="none")
        state = {"text": ""}

        def generate():
            idx = options.index(student_var.get())
            cert = CertificateService.build(students[idx], self.courses.trainers)
            text = CertificateService.render_text(cert)
            cert_box.configure(state="normal")
            cert_box.delete("1.0", tk.END)
            cert_box.insert("1.0", text)
            cert_box.configure(state="disabled")
            cert_box.pack(fill=tk.BOTH, expand=True, pady=(14, 0))
            state["text"] = text

        def save_file():
            if not state["text"]:
                messagebox.showinfo("Certificate", "Generate a certificate first.")
                return
            path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text file", "*.txt")],
                                                 initialfile="certificate.txt")
            if path:
                Path(path).write_text(state["text"])
                messagebox.showinfo("Certificate", f"Saved to {path}")

        self._action_button(card, "Generate Certificate", generate)
        self._action_button(card, "Save as .txt", save_file, primary=False)

    # ------------------------------------------------------- Analytics
    def show_analytics(self) -> None:
        self._clear_content()
        self._panel_header("Analytics Dashboard", "Bonus - a live desktop-style report rolled up from every module")

        summary = AnalyticsService.summary(self.registry, self.courses, self.attendance)

        kpi_frame = tk.Frame(self.content, bg=self.c["bg"])
        kpi_frame.pack(fill=tk.X, pady=(0, 14))
        kpis = [
            ("\U0001F465", "Total Students", str(summary["total_students"]), self.c["operator_bg"]),
            ("\U0001F4DA", "Active Courses", str(summary["total_courses"]), self.c["accent_bg"]),
            ("\U0001F4C5", f"Attendance ({summary['attendance_status']})",
             f"{summary['attendance_pct']}%", self.c["button_bg"]),
            ("\U0001F4B0", "Projected Revenue", f"{summary['revenue']:.0f}", self.c["accent2"]),
        ]
        for icon, label, value, tint in kpis:
            kpi = tk.Frame(kpi_frame, bg=self.c["display_bg"], padx=16, pady=14,
                          highlightbackground=self.c["border"], highlightthickness=1)
            kpi.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 10))
            tk.Frame(kpi, bg=tint, height=3).pack(fill=tk.X, side=tk.TOP, anchor="n")
            top_row = tk.Frame(kpi, bg=self.c["display_bg"])
            top_row.pack(fill=tk.X, pady=(10, 0))
            tk.Label(top_row, text=icon, font=("Segoe UI Emoji", 16),
                     bg=self.c["display_bg"]).pack(side=tk.LEFT, padx=(0, 6))
            tk.Label(top_row, text=value, font=("Segoe UI", 18, "bold"), bg=self.c["display_bg"],
                     fg=self.c["display_fg"]).pack(side=tk.LEFT, anchor="w")
            tk.Label(kpi, text=label, font=("Segoe UI", 9, "bold"), bg=self.c["display_bg"],
                     fg=tint).pack(anchor="w", pady=(4, 0))

        card = self._card()
        tk.Label(card, text="Enrollment by course", font=("Segoe UI", 12, "bold"),
                 bg=self.c["display_bg"], fg=self.c["display_fg"]).pack(anchor="w", pady=(0, 10))

        if not summary["per_course"]:
            tk.Label(card, text="No enrollments yet.", bg=self.c["display_bg"],
                     fg=self.c["accent_bg"], font=("Segoe UI", 10, "italic")).pack(anchor="w")
            return

        bar_max_width = 320
        canvas_height = 32 * len(summary["per_course"]) + 10
        canvas = tk.Canvas(card, bg=self.c["display_bg"], height=canvas_height, highlightthickness=0)
        canvas.pack(fill=tk.X, pady=(4, 0))
        for i, (name, count, _fee) in enumerate(summary["per_course"]):
            y = 16 + i * 32
            canvas.create_text(6, y, anchor="w", text=name, fill=self.c["display_fg"], font=("Segoe UI", 10, "bold"))
            bar_w = int((count / summary["max_count"]) * bar_max_width) if summary["max_count"] else 0
            canvas.create_rectangle(170, y - 8, 170 + max(bar_w, 2), y + 8, fill=self.c["operator_bg"], outline="")
            canvas.create_text(170 + bar_max_width + 20, y, anchor="w", text=str(count),
                                fill=self.c["display_fg"], font=("Segoe UI", 10, "bold"))

    # ------------------------------------------------------- Assignments
    def show_assignments(self) -> None:
        self._clear_content()
        self._panel_header("Assignments & Deadlines", "Bonus - track coursework across every batch")

        toolbar = tk.Frame(self.content, bg=self.c["bg"])
        toolbar.pack(fill=tk.X)
        add_btn = tk.Button(toolbar, text="+ New Assignment", bg=self.c["operator_bg"], fg=self.c["operator_fg"],
                             font=("Segoe UI", 10, "bold"), bd=0, relief="flat")
        add_btn.pack(side=tk.LEFT, ipady=6, ipadx=10)
        self._bind_hover(add_btn, self.c["operator_bg"])

        tree = self._styled_treeview(self.content, ["Title", "Course", "Due", "Status"])

        def refresh():
            tree.delete(*tree.get_children())
            for a in self.assignments.all():
                label, _tone = AssignmentService.status(a)
                tree.insert("", tk.END, iid=a["id"], values=(a["title"], a["course"], a["due"].isoformat(), label))

        def toggle_selected():
            sel = tree.selection()
            if not sel:
                messagebox.showinfo("Assignments", "Select an assignment row first.")
                return
            self.assignments.toggle(sel[0])
            refresh()

        def remove_selected():
            sel = tree.selection()
            if not sel:
                messagebox.showinfo("Assignments", "Select an assignment row first.")
                return
            self.assignments.remove(sel[0])
            refresh()

        def add_assignment():
            title = simpledialog.askstring("New Assignment", "Title:", parent=self.root)
            if not title:
                return
            course = simpledialog.askstring(
                "New Assignment", f"Course ({', '.join(self.courses.course_names())}):", parent=self.root)
            due = simpledialog.askstring("New Assignment", "Due date (YYYY-MM-DD):", parent=self.root)
            try:
                self.assignments.add(title, course, due, self.courses.course_names())
                refresh()
            except ELearningError as exc:
                messagebox.showerror("Assignment Error", str(exc))

        add_btn.configure(command=add_assignment)

        action_row = tk.Frame(self.content, bg=self.c["bg"])
        action_row.pack(fill=tk.X, pady=(10, 0))
        for label, cmd in [("Toggle Done", toggle_selected), ("Remove", remove_selected)]:
            btn = tk.Button(action_row, text=label, command=cmd, bg=self.c["button_bg"], fg=self.c["button_fg"],
                            font=("Segoe UI", 10, "bold"), bd=0, relief="flat")
            btn.pack(side=tk.LEFT, padx=(0, 8), ipady=6, ipadx=10)
            self._bind_hover(btn, self.c["button_bg"])

        refresh()

    # ------------------------------------------------------- Leaderboard
    def show_leaderboard(self) -> None:
        self._clear_content()
        self._panel_header("Leaderboard", "Bonus - gamified engagement ranking across all registered learners")

        rows = LeaderboardService.rows(self.registry)
        if not rows:
            tk.Label(self.content, text="No students yet - register a few learners to populate the leaderboard.",
                     bg=self.c["bg"], fg=self.c["accent_bg"], font=("Segoe UI", 10, "italic")).pack(anchor="w")
            return

        tree = self._styled_treeview(self.content, ["Rank", "Name", "Course", "Score", "Badge"])
        for i, (name, course, score, badge) in enumerate(rows, start=1):
            tree.insert("", tk.END, values=(i, name, course, score, badge))

    # ------------------------------------------------------- Forum
    def show_forum(self) -> None:
        self._clear_content()
        self._panel_header("Discussion Forum", "Bonus - course-scoped Q&A, ask and upvote the best answers")

        course_names = self.courses.course_names()
        course_var, combo = self._labeled_combo(self.content, "Course", course_names)

        tree = self._styled_treeview(self.content, ["Votes", "Question", "Author", "Replies"])

        def refresh():
            tree.delete(*tree.get_children())
            for t in self.forum.by_course(course_var.get()):
                tree.insert("", tk.END, iid=t["id"], values=(t["votes"], t["question"], t["author"], len(t["replies"])))

        def upvote_selected():
            sel = tree.selection()
            if not sel:
                messagebox.showinfo("Forum", "Select a question row first.")
                return
            self.forum.upvote(sel[0])
            refresh()

        def reply_selected():
            sel = tree.selection()
            if not sel:
                messagebox.showinfo("Forum", "Select a question row first.")
                return
            author = simpledialog.askstring("Reply", "Your name:", parent=self.root) or "You"
            text = simpledialog.askstring("Reply", "Your reply:", parent=self.root)
            if not text:
                return
            try:
                self.forum.reply(sel[0], author, text)
                refresh()
            except ELearningError as exc:
                messagebox.showerror("Forum Error", str(exc))

        def ask_question():
            course = simpledialog.askstring(
                "Ask a Question", f"Course ({', '.join(course_names)}):", parent=self.root)
            author = simpledialog.askstring("Ask a Question", "Your name:", parent=self.root)
            question = simpledialog.askstring("Ask a Question", "Question:", parent=self.root)
            try:
                self.forum.ask(course, author, question, course_names)
                if course in course_names:
                    course_var.set(course)
                refresh()
            except ELearningError as exc:
                messagebox.showerror("Forum Error", str(exc))

        combo.bind("<<ComboboxSelected>>", lambda e: refresh())

        action_row = tk.Frame(self.content, bg=self.c["bg"])
        action_row.pack(fill=tk.X, pady=(10, 0))
        for label, cmd in [("Ask Question", ask_question), ("Upvote", upvote_selected), ("Reply", reply_selected)]:
            btn = tk.Button(action_row, text=label, command=cmd, bg=self.c["operator_bg"], fg=self.c["operator_fg"],
                            font=("Segoe UI", 10, "bold"), bd=0, relief="flat")
            btn.pack(side=tk.LEFT, padx=(0, 8), ipady=6, ipadx=10)
            self._bind_hover(btn, self.c["operator_bg"])

        refresh()

    # ------------------------------------------------------- Study Notes
    def show_notes(self) -> None:
        self._clear_content()
        self._panel_header("Study Notes", "Bonus - a searchable notes library you can pin and filter by course")

        toolbar = tk.Frame(self.content, bg=self.c["bg"])
        toolbar.pack(fill=tk.X)

        search_var = tk.StringVar()
        search_entry = tk.Entry(toolbar, textvariable=search_var, font=("Segoe UI", 10),
                                 bd=1, relief="solid", width=28)
        search_entry.pack(side=tk.LEFT, ipady=5, padx=(0, 8))

        course_var = tk.StringVar(value="All")
        course_combo = ttk.Combobox(toolbar, textvariable=course_var, values=["All"] + self.courses.course_names(),
                                     state="readonly", width=16)
        course_combo.pack(side=tk.LEFT, padx=(0, 8))

        add_btn = tk.Button(toolbar, text="+ New Note", bg=self.c["operator_bg"], fg=self.c["operator_fg"],
                             font=("Segoe UI", 10, "bold"), bd=0, relief="flat")
        add_btn.pack(side=tk.LEFT, ipady=6, ipadx=10)
        self._bind_hover(add_btn, self.c["operator_bg"])

        tree = self._styled_treeview(self.content, ["Pinned", "Course", "Title", "Note"])

        def refresh():
            tree.delete(*tree.get_children())
            for n in self.notes.search(search_var.get(), course_var.get()):
                pin_mark = "★" if n["pinned"] else ""
                tree.insert("", tk.END, iid=n["id"], values=(pin_mark, n["course"], n["title"], n["body"][:60]))

        def toggle_pin_selected():
            sel = tree.selection()
            if not sel:
                messagebox.showinfo("Notes", "Select a note row first.")
                return
            self.notes.toggle_pin(sel[0])
            refresh()

        def remove_selected():
            sel = tree.selection()
            if not sel:
                messagebox.showinfo("Notes", "Select a note row first.")
                return
            self.notes.remove(sel[0])
            refresh()

        def add_note():
            course = simpledialog.askstring(
                "New Note", f"Course ({', '.join(self.courses.course_names())}):", parent=self.root)
            title = simpledialog.askstring("New Note", "Title:", parent=self.root)
            body = simpledialog.askstring("New Note", "Note content:", parent=self.root)
            try:
                self.notes.add(course, title, body, self.courses.course_names())
                refresh()
            except ELearningError as exc:
                messagebox.showerror("Notes Error", str(exc))

        add_btn.configure(command=add_note)
        search_entry.bind("<KeyRelease>", lambda e: refresh())
        course_combo.bind("<<ComboboxSelected>>", lambda e: refresh())

        action_row = tk.Frame(self.content, bg=self.c["bg"])
        action_row.pack(fill=tk.X, pady=(10, 0))
        for label, cmd in [("Toggle Pin", toggle_pin_selected), ("Remove", remove_selected)]:
            btn = tk.Button(action_row, text=label, command=cmd, bg=self.c["button_bg"], fg=self.c["button_fg"],
                            font=("Segoe UI", 10, "bold"), bd=0, relief="flat")
            btn.pack(side=tk.LEFT, padx=(0, 8), ipady=6, ipadx=10)
            self._bind_hover(btn, self.c["button_bg"])

        refresh()

    # ------------------------------------------------------- Student IDs
    def show_ids(self) -> None:
        self._clear_content()
        self._panel_header("Student ID Generator", "Task 17 - bulk ID generation")
        card = self._card()

        start_var, _ = self._labeled_entry(card, "Start ID")
        count_var, count_entry = self._labeled_entry(card, "Count")
        start_var.set("1001")
        count_var.set("20")

        listbox = tk.Listbox(card, font=("Consolas", 10), bd=0, height=8,
                              bg=self.c["bg"], fg=self.c["display_fg"])

        def submit(event=None):
            try:
                ids = IDGeneratorService.generate(start_var.get(), count_var.get())
                listbox.delete(0, tk.END)
                for sid in ids:
                    listbox.insert(tk.END, sid)
                listbox.pack(fill=tk.BOTH, expand=True, pady=(14, 0))
            except ELearningError as exc:
                self._banner(card, str(exc), success=False)

        def copy_all():
            self.root.clipboard_clear()
            self.root.clipboard_append("\n".join(listbox.get(0, tk.END)))

        count_entry.bind("<Return>", submit)
        self._action_button(card, "Generate IDs", submit)
        self._action_button(card, "Copy All", copy_all, primary=False)

    # ------------------------------------------------------- Dashboard
    def show_dashboard(self) -> None:
        self._clear_content()
        self._panel_header("Role Dashboard", "Task 23 & 24 - inheritance and polymorphism in action")
        card = self._card()

        role_var, _ = self._labeled_combo(card, "Role", ["Student", "Instructor", "Admin"])
        listbox = tk.Listbox(card, font=("Segoe UI", 10), bd=0, height=6,
                              bg=self.c["bg"], fg=self.c["display_fg"])

        def submit():
            role = role_var.get()
            if role == "Student":
                sample = Student("Arfa", 21, "arfa@gmail.com", "Python")
                sample.enroll("Data Analytics")
            elif role == "Instructor":
                sample = Instructor("Ahmed", 5, "Python")
                sample.upload_course("Python Programming")
                sample.upload_course("AI Fundamentals")
            else:
                sample = Admin("Sara")
            listbox.delete(0, tk.END)
            listbox.insert(tk.END, sample.login_message())
            for line in sample.dashboard():
                listbox.insert(tk.END, line)
            listbox.pack(fill=tk.BOTH, expand=True, pady=(14, 0))

        self._action_button(card, "Show Dashboard", submit)

    # ------------------------------------------------------------ Exit
    def _on_close(self) -> None:
        self.persistence.save({
            "students": self.registry.to_json(),
            "courses": self.courses.to_json(),
            "assignments": self.assignments.to_json(),
            "forum": self.forum.to_json(),
            "notes": self.notes.to_json(),
        })
        self.root.destroy()


# =============================================================================
# ENTRY POINT
# =============================================================================
def main() -> None:
    root = tk.Tk()
    ELearningApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
