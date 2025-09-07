import tkinter as tk
import json
import requests
import os
import time
import random
import html
from tkinter import messagebox,simpledialog,ttk
#file paths
USERS_FILE="users.json"
QUESTIONS_FILE="questions.json"
CONFIG_FILE="config.json"
SCORES_FILE="scores.json"

#file setup
def init_files():
    if not os.path.exists(USERS_FILE):
        save_json(USERS_FILE, {"admin":{"password":"admin","role":"admin"}})
    if not os.path.exists(QUESTIONS_FILE):
        save_json(QUESTIONS_FILE,
                  {
                      "Geography":[],"Science":[],"Art":[],"Math":[],"History":[]
                  }
                  )
    if not os.path.exists(CONFIG_FILE):
        save_json(CONFIG_FILE, {
            "retakes_allowed": True,
            "user_settings": {}
        })

    if not os.path.exists(SCORES_FILE):
        save_json(SCORES_FILE, {})
def load_json(filename):
    with open(filename,"r")as f: return json.load(f)
def save_json(filename,data):
    with open(filename, "w")as f:json.dump(data, f, indent=4) 

#main app
class QuizApp:
    def __init__(self, root):
        self.root=root
        self.root.title("quizapplication")
        self.root.geometry("500x400")
        self.user=None
        self.show_login()
    def clear_window(self):
        for widget in self.root.winfo_children():
            widget.destroy()
    #login
    def show_login(self):
        self.clear_window()
        tk.Label(self.root,text="Login").pack(pady=20)
        tk.Label(self.root,text="Username").pack()
        username_entry=tk.Entry(self.root)
        username_entry.pack()
        tk.Label(self.root,text="Password").pack()
        password_entry=tk.Entry(self.root)
        password_entry.pack()

        def attempt_login():
            users=load_json(USERS_FILE)
            username=username_entry.get()
            password=password_entry.get()
            if username in users and users[username]["password"]==password:
                self.user={"username":username,"role":users[username]["role"]}
                if self.user["role"]=="admin":
                    self.show_admin_panel()
                else:
                    self.show_user_panel()
            else:messagebox.showerror("Error","invalid username/password")
        tk.Button(self.root,text="Login",command=attempt_login).pack(pady=10)
    #admin panel
    def show_admin_panel(self):
        self.clear_window()
        tk.Label(self.root, text="Admin Panel", font=("Helvetica", 16)).pack(pady=10)
        tk.Button(self.root, text="Add Student", width=30, command=self.add_student).pack(pady=5)
        tk.Button(self.root, text="Set Timers & Categories", width=30, command=self.set_user_settings).pack(pady=5)
        tk.Button(self.root, text="Manage Questions", width=30, command=self.manage_questions).pack(pady=5)
        tk.Button(self.root, text="Fetch Online Questions", width=30, command=self.fetch_questions).pack(pady=5)
        tk.Button(self.root, text="View Scores", width=30, command=self.view_scores).pack(pady=5)
        tk.Button(self.root, text="Toogle Retakes", width=30, command=self.toogle_retakes).pack(pady=5)
        tk.Button(self.root, text="Logout", width=30, command=self.show_login).pack(pady=5)

    def add_student(self):
        username = simpledialog.askstring("Add Student", "Enter username:")
        if not username:
            return
        password = simpledialog.askstring("Password", f"Set password for {username}:")
        if not password:
            return
        users = load_json(USERS_FILE)
        if username in users:
            messagebox.showerror("Error", "Username already exists.")
            return
        users[username] = {"password": password, "role": "user"}
        save_json(USERS_FILE, users)
        messagebox.showinfo("Success", f"Student '{username}' added.")

    def set_user_settings(self):
        users = load_json(USERS_FILE)
        config = load_json(CONFIG_FILE)

        for username, details in users.items():
            if details["role"] == "user":
                mins = simpledialog.askinteger("Timer", f"Set time (minutes) for {username} (0 = no limit):", minvalue=0)
                cats = simpledialog.askstring("Categories", f"Allowed categories for {username} (comma separated):")

                if mins is not None and cats:
                    config["user_settings"][username] = {
                        "timer": mins,
                        "allowed_categories": [c.strip() for c in cats.split(",")]
                    }

        save_json(CONFIG_FILE, config)
        messagebox.showinfo("Saved", "User settings updated.")
    def toogle_retakes(self):
        config = load_json(CONFIG_FILE)
        config["retakes_allowed"] = not config["retakes_allowed"]
        save_json(CONFIG_FILE, config)

        status = "enabled" if config["retakes_allowed"] else "disabled"
        messagebox.showinfo("Retakes", f"Retakes are now {status}.")
    def manage_questions(self):
        questions = load_json(QUESTIONS_FILE)

        win = tk.Toplevel(self.root)
        win.title("Manage Questions")
        win.geometry("600x500")

        category_var = tk.StringVar(value="Geography")
        dropdown = ttk.Combobox(win, textvariable=category_var, values=list(questions.keys()))
        dropdown.pack(pady=10)

        listbox = tk.Listbox(win, width=80)
        listbox.pack(pady=10)

        def refresh():
            listbox.delete(0, tk.END)
            for i, q in enumerate(questions[category_var.get()]):
                listbox.insert(tk.END, f"{i+1}. {q['question']}")

        def add():
            cat = category_var.get()
            q_text = simpledialog.askstring("Question", "Enter question:")
            if not q_text:
                return

            options = []
            for opt in ["A", "B", "C", "D"]:
                ans = simpledialog.askstring("Option", f"Option {opt}:")
                options.append(f"{opt}. {ans}")

            correct = simpledialog.askstring("Answer", "Correct option (A-D):")
            if not correct or correct.upper() not in "ABCD":
                return messagebox.showerror("Error", "Answer must be A-D")

            questions[cat].append({"question": q_text, "options": options, "answer": correct.upper()})
            save_json(QUESTIONS_FILE, questions)
            refresh()

        def delete():
            sel = listbox.curselection()
            if sel:
                del questions[category_var.get()][sel[0]]
                save_json(QUESTIONS_FILE, questions)
                refresh()

        tk.Button(win, text="Add", command=add).pack()
        tk.Button(win, text="Delete", command=delete).pack()
        dropdown.bind("<<ComboboxSelected>>", lambda e: refresh())
        refresh()

    def fetch_questions(self):
        category_map = {
            "Science": 17,
            "Math": 19,
            "History": 23,
            "Geography": 22,
            "Art": 25
        }

        cat = simpledialog.askstring("Fetch", f"Choose category ({', '.join(category_map.keys())}):")
        if not cat or cat not in category_map:
            return

        total = simpledialog.askinteger("Number", "How many questions?", minvalue=1, maxvalue=200)
        if not total:
            return

        questions = load_json(QUESTIONS_FILE)
        cat_id = category_map[cat]
        fetched = 0

        while fetched < total:
            amount = min(50, total - fetched)
            url = f"https://opentdb.com/api.php?amount={amount}&category={cat_id}&type=multiple"

            try:
                res = requests.get(url, timeout=5)
                data = res.json()

                for item in data["results"]:
                    text = html.unescape(item["question"])
                    correct = html.unescape(item["correct_answer"])
                    incorrects = [html.unescape(x) for x in item["incorrect_answers"]]

                    options = incorrects + [correct]
                    random.shuffle(options)

                    labels = [f"{chr(65+i)}. {opt}" for i, opt in enumerate(options)]
                    answer = chr(65 + options.index(correct))

                    if text not in [q["question"] for q in questions[cat]]:
                        questions[cat].append({"question": text, "options": labels, "answer": answer})

                fetched += amount

            except Exception as e:
                return messagebox.showerror("Error", f"Failed: {e}")

        save_json(QUESTIONS_FILE, questions)
        messagebox.showinfo("Done", f"Fetched {fetched} {cat} questions.")

    def view_scores(self):
        scores = load_json(SCORES_FILE)
        win = tk.Toplevel(self.root)
        win.title("Scores")
        for u, data in scores.items():
            tk.Label(win, text=f"{u}: {data}").pack()
    
    #user panel
    def show_user_panel(self):
        self.clear_window()
        tk.Label(self.root, text=f"Welcome, {self.user['username']}", font=("Helvetica", 16)).pack(pady=10)

        config = load_json(CONFIG_FILE)
        settings = config["user_settings"].get(self.user["username"], {})
        allowed = settings.get("allowed_categories", [])

        if not allowed:
            tk.Label(self.root, text="No categories assigned. Contact admin.").pack()
            tk.Button(self.root, text="Logout", command=self.show_login).pack()
            return

        tk.Label(self.root, text="Select category:").pack()
        category_var = tk.StringVar()
        ttk.Combobox(self.root, textvariable=category_var, values=allowed).pack(pady=5)

        tk.Button(self.root, text="Start Quiz", command=lambda: self.start_quiz(category_var.get())).pack(pady=10)
        tk.Button(self.root, text="Logout", command=self.show_login).pack(pady=5)
    def start_quiz(self,category):
        questions = load_json(QUESTIONS_FILE)
        config = load_json(CONFIG_FILE)
        scores = load_json(SCORES_FILE)
        user = self.user["username"]

        if not questions.get(category):
            return messagebox.showinfo("Empty", f"No questions in {category}")

        if not config["retakes_allowed"] and user in scores:
            return messagebox.showwarning("No Retakes", "You already took the quiz")

        timer = config["user_settings"].get(user, {}).get("timer", 0)
        time_limit = timer * 60 if timer else None
        start_time = time.time()
        score = 0

        win = tk.Toplevel(self.root)
        win.title(f"{category} Quiz")

        question_index = [0]
        question_label = tk.Label(win, wraplength=400, font=("Arial", 12))
        question_label.pack(pady=20)

        option_var = tk.StringVar()
        option_buttons = []
        for _ in range(4):
            btn = tk.Radiobutton(win, variable=option_var, font=("Arial", 10), anchor="w")
            btn.pack(anchor="w")
            option_buttons.append(btn)

        def show_question():
            if time_limit and time.time() - start_time >= time_limit:
                return end_quiz()

            if question_index[0] >= len(questions[category]):
                return end_quiz()

            q = questions[category][question_index[0]]
            question_label.config(text=f"Q{question_index[0]+1}: {q['question']}")
            option_var.set(None)

            for i, opt in enumerate(q['options']):
                option_buttons[i].config(text=opt, value=opt[0])

        def submit_answer():
            nonlocal score
            q = questions[category][question_index[0]]
            if option_var.get() == q['answer']:
                score += 1
            question_index[0] += 1
            show_question()

        def end_quiz():
            win.destroy()
            total = len(questions[category])
            pct = (score / total) * 100
            scores[user] = {"score": score, "total": total, "percentage": f"{pct:.1f}%", "category": category}
            save_json(SCORES_FILE, scores)
            messagebox.showinfo("Done", f"Score: {score}/{total} ({pct:.1f}%)")

        tk.Button(win, text="Submit", command=submit_answer).pack(pady=10)
        show_question()

#runapp
if __name__=="__main__":
    init_files()
    root=tk.Tk()
    QuizApp(root)
    root.mainloop()
