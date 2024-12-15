import random
from docx import Document
import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox
from tkinter import filedialog


ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")


def center_window(win, width=None, height=None):
    win.update_idletasks()
    screen_width = win.winfo_screenwidth()
    screen_height = win.winfo_screenheight()

    if width is None or height is None:
        current_geometry = win.geometry()
        wh_part = current_geometry.split('+')[0]
        w_str, h_str = wh_part.split('x')
        width = int(w_str)
        height = int(h_str)

    x = (screen_width - width) // 2
    y = (screen_height - height) // 2
    win.geometry(f"{width}x{height}+{x}+{y}")


root = ctk.CTk()
root.title("Тестирование")
root.geometry("900x600")
center_window(root, 500, 300)


def parse_questions(file_name):
    document = Document(file_name)
    questions = []
    current_question = None
    for paragraph in document.paragraphs:
        text = paragraph.text.strip()
        if text.startswith("<question>"):
            if current_question:
                questions.append(current_question)
            current_question = {
                "question": text.replace("<question>", "").strip(),
                "variants": [],
                "correct_index": 0
            }
        elif text.startswith("<variant>") and current_question:
            current_question["variants"].append(text.replace("<variant>", "").strip())
    if current_question:
        questions.append(current_question)
    return questions


def start_test():
    try:
        num_questions_str = question_count_var.get().strip()
        if not num_questions_str.isdigit():
            raise ValueError("Введите число.")
        num_questions = int(num_questions_str)
        if num_questions <= 0:
            raise ValueError("Количество вопросов должно быть положительным числом.")

        questions = parse_questions("URBU.docx")
        if not questions:
            raise ValueError("В файле нет вопросов или они неверно отформатированы.")
    except ValueError as ve:
        messagebox.showerror("Ошибка", f"Некорректное значение: {ve}")
        return
    except Exception as e:
        messagebox.showerror("Ошибка", f"Не удалось загрузить вопросы: {e}")
        return

    shuffled_questions = random.sample(questions, k=min(num_questions, len(questions)))
    root.withdraw()
    TestWindow(shuffled_questions, shuffle_answers_var.get())


def export_incorrect_answers(results):
    # Фильтруем только неправильные ответы
    incorrect_results = [r for r in results if not r["is_correct"]]
    if not incorrect_results:
        messagebox.showinfo("Информация", "Нет неправильных ответов для экспорта.")
        return

    # Открываем файловый диалог для выбора пути сохранения
    file_path = filedialog.asksaveasfilename(
        defaultextension=".docx",
        filetypes=[("Word Documents", "*.docx"), ("All Files", "*.*")],
        title="Сохранить файл как"
    )
    if not file_path:  # Если пользователь закрыл диалог без выбора
        return

    # Создаем документ Word
    document = Document()
    document.add_heading("Неправильные ответы", level=1)

    for result in incorrect_results:
        document.add_heading(result["question"], level=2)
        document.add_paragraph(f"{result['correct']}")

    # Сохраняем файл по указанному пути
    try:
        document.save(file_path)
        messagebox.showinfo("Экспорт завершен", f"Файл успешно сохранен: {file_path}")
    except Exception as e:
        messagebox.showerror("Ошибка", f"Не удалось сохранить файл: {e}")



class TestWindow(ctk.CTkToplevel):
    def __init__(self, questions, shuffle_answers):
        super().__init__()
        self.questions = questions
        self.shuffle_answers = shuffle_answers
        self.current_question = 0
        self.score = 0
        self.results = []
        self.time_remaining = 50 * 60  # 50 минут в секундах

        self.title("Тестирование")
        self.geometry("600x400")
        self.center_window()
        self.protocol("WM_DELETE_WINDOW", self.close_test)

        self.create_widgets()
        self.start_timer()
        self.show_question()

    def center_window(self):
        center_window(self, 1300, 700)

    def create_widgets(self):
        self.main_frame = ctk.CTkFrame(self, corner_radius=15)
        self.main_frame.pack(expand=True, fill="both", padx=20, pady=20)

        self.timer_label = ctk.CTkLabel(self.main_frame, text="", font=("Arial", 20, "bold"), text_color="red")
        self.timer_label.pack(pady=5)

        self.question_label = ctk.CTkLabel(self.main_frame, text="", wraplength=1000, justify="left",
                                           font=("Arial", 14, "bold"))
        self.question_label.pack(pady=10)

        self.options_frame = ctk.CTkFrame(self.main_frame, corner_radius=10)
        self.options_frame.pack(pady=10, fill="x")

        buttons_frame = ctk.CTkFrame(self.main_frame, corner_radius=10)
        buttons_frame.pack(pady=10, fill="x", side="bottom")

        self.next_button = ctk.CTkButton(
            buttons_frame,
            text="Далее",
            font=("Arial", 16),
            command=self.next_question,
            width=200,
            height=50
        )
        self.next_button.pack(side="left", padx=10)

        self.show_answer_button = ctk.CTkButton(
            buttons_frame,
            text="Показать ответ",
            font=("Arial", 16),
            command=self.show_correct_answer,
            width=200,
            height=50
        )
        self.show_answer_button.pack(side="right", padx=10)

    def show_correct_answer(self):
        correct_answer = self.questions[self.current_question]["variants"][0]
        messagebox.showinfo("Правильный ответ", f"Правильный ответ: {correct_answer}")

    def start_timer(self):
        def update_timer():
            if self.time_remaining > 0:
                mins, secs = divmod(self.time_remaining, 60)
                timer_text = f"Оставшееся время: {mins:02d}:{secs:02d}"
                self.timer_label.configure(text=timer_text)
                self.time_remaining -= 1
                self.after(1000, update_timer)
            else:
                self.finish_test()

        update_timer()

    def show_question(self):
        question = self.questions[self.current_question]
        question_number = f"Вопрос {self.current_question + 1} из {len(self.questions)}:"
        self.question_label.configure(text=f"{question_number}\n\n{question['question']}", font=("Arial", 18, "bold"))

        for widget in self.options_frame.winfo_children():
            widget.destroy()

        self.variants = question["variants"][:]
        if self.shuffle_answers:
            original_variants = self.variants[:]
            random.shuffle(self.variants)
            self.correct_index = self.variants.index(original_variants[0])
        else:
            self.correct_index = 0

        self.selected_answer = ctk.IntVar(value=-1)

        for i, variant in enumerate(self.variants):
            row_frame = ctk.CTkFrame(self.options_frame)
            row_frame.pack(fill="x", padx=10, pady=10)

            rb = tk.Radiobutton(
                row_frame,
                variable=self.selected_answer,
                value=i,
                font=("Arial", 55)
            )
            rb.pack(side="left", padx=10, pady=10)

            textbox = ctk.CTkTextbox(
                row_frame,
                wrap="word",
                height=100,
                width=900
            )
            textbox.insert("1.0", variant)
            textbox.configure(state="disabled", font=("Arial", 22))
            textbox.pack(side="left", fill="x", expand=True, padx=10)

    def next_question(self):
        selected_index = self.selected_answer.get()
        if selected_index == -1:
            messagebox.showwarning("Внимание", "Выберите ответ!")
            return

        is_correct = (selected_index == self.correct_index)
        self.results.append({
            "question": self.questions[self.current_question]["question"],
            "variants": self.questions[self.current_question]["variants"],  # Сохраняем оригинальные варианты
            "selected": self.variants[selected_index],
            "correct": self.variants[self.correct_index],
            "is_correct": is_correct
        })

        if is_correct:
            self.score += 4

        self.current_question += 1
        if self.current_question < len(self.questions):
            self.show_question()
        else:
            self.finish_test()

    def finish_test(self):
        self.withdraw()

        incorrect_results = [r for r in self.results if not r["is_correct"]]
        incorrect_questions = [
            {
                "question": r["question"],
                "variants": r["variants"],
                "correct_index": r["variants"].index(r["correct"])
            }
            for r in incorrect_results
        ]

        results_window = tk.Toplevel(root)
        results_window.title("Детали теста")
        results_window.geometry("900x700")
        center_window(results_window, 900, 700)

        results_frame = tk.Frame(results_window, bg="white", bd=2, relief="groove")
        results_frame.pack(expand=True, fill="both", padx=20, pady=20)

        title_label = tk.Label(
            results_frame,
            text="Результаты теста",
            font=("Arial", 22, "bold"),
            bg="white",
            fg="black"
        )
        title_label.pack(pady=(20, 20))

        results_text = tk.Text(
            results_frame,
            wrap="word",
            font=("Arial", 16),
            height=25,
            width=80,
            padx=10,
            pady=10
        )
        results_text.pack(expand=True, fill="both", padx=10, pady=10)

        correct_count = sum(r['is_correct'] for r in self.results)
        total_count = len(self.results)
        percentage = (correct_count / total_count) * 100 if total_count > 0 else 0

        results_text.insert(
            "end",
            f"Вы ответили правильно на {correct_count} из {total_count} вопросов ({percentage:.2f}%)\n\n",
            "header"
        )
        results_text.insert("end", "=" * 50 + "\n\n")

        for i, result in enumerate(self.results):
            results_text.insert("end", f"Вопрос {i + 1}: {result['question']}\n", "question")
            results_text.insert("end", f"  Ваш ответ: {result['selected']}\n", "selected")
            results_text.insert("end", f"  Правильный ответ: {result['correct']}\n", "correct")
            if result['is_correct']:
                results_text.insert("end", "  Результат: Правильно\n\n", "correct_info")
            else:
                results_text.insert("end", "  Результат: Неправильно\n\n", "wrong_info")
            results_text.insert("end", "-" * 50 + "\n\n")

        results_text.tag_config("header", foreground="black", font=("Arial", 18, "bold"))
        results_text.tag_config("question", foreground="black", font=("Arial", 16, "italic"))
        results_text.tag_config("selected", foreground="blue", font=("Arial", 16))
        results_text.tag_config("correct", foreground="green", font=("Arial", 16))
        results_text.tag_config("correct_info", foreground="darkgreen", font=("Arial", 16, "bold"))
        results_text.tag_config("wrong_info", foreground="red", font=("Arial", 16, "bold"))
        results_text.configure(state="normal")

        buttons_frame = tk.Frame(results_frame, bg="white")
        buttons_frame.pack(pady=10)

        export_button = tk.Button(
            buttons_frame,
            text="Экспортировать неправильные ответы",
            font=("Arial", 14),
            command=lambda: export_incorrect_answers(self.results)
        )
        export_button.pack(side="left", padx=10)

        if incorrect_results:
            retry_button = tk.Button(
                buttons_frame,
                text="Пройти заново (ошибки)",
                font=("Arial", 14),
                command=lambda: self.retry_with_incorrect(incorrect_questions, results_window)
            )
            retry_button.pack(side="left", padx=10)

        close_button = tk.Button(
            buttons_frame,
            text="Закрыть",
            font=("Arial", 14),
            command=lambda: self.close_results_window(results_window)
        )
        close_button.pack(side="left", padx=10)

    def retry_with_incorrect(self, incorrect_questions, results_window):
        results_window.destroy()
        self.destroy()
        TestWindow(incorrect_questions, self.shuffle_answers)

    def close_results_window(self, results_window):
        results_window.destroy()
        root.deiconify()
        self.destroy()

    def close_test(self):
        root.deiconify()
        self.destroy()


main_frame = ctk.CTkFrame(root, corner_radius=15)
main_frame.pack(expand=True, fill="both", padx=20, pady=20)

header_label = ctk.CTkLabel(main_frame, text="Добро пожаловать в систему тестирования", font=("Arial", 18, "bold"))
header_label.pack(pady=10)

input_frame = ctk.CTkFrame(main_frame)
input_frame.pack(pady=10)

ctk.CTkLabel(input_frame, text="Количество вопросов:", font=("Arial", 14)).grid(row=0, column=0, padx=10, pady=10, sticky="e")

question_count_var = ctk.StringVar(value="25")
question_count_entry = ctk.CTkEntry(input_frame, textvariable=question_count_var, width=100)
question_count_entry.grid(row=0, column=1, padx=10, pady=10)

ctk.CTkLabel(input_frame, text="Перемешивать варианты ответов?", font=("Arial", 14)).grid(row=1, column=0, padx=10, pady=10, sticky="e")

shuffle_answers_var = ctk.BooleanVar(value=True)
shuffle_checkbox = ctk.CTkCheckBox(input_frame, text="Да", variable=shuffle_answers_var)
shuffle_checkbox.grid(row=1, column=1, padx=10, pady=10)

start_button = ctk.CTkButton(main_frame, text="Начать тест", command=start_test)
start_button.pack(pady=20)

root.mainloop()