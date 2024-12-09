import random
from docx import Document
import customtkinter as ctk

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
root.geometry("500x300")
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
        ctk.CTkMessagebox.show_error("Ошибка", f"Некорректное значение: {ve}")
        return
    except Exception as e:
        ctk.CTkMessagebox.show_error("Ошибка", f"Не удалось загрузить вопросы: {e}")
        return

    shuffled_questions = random.sample(questions, k=min(num_questions, len(questions)))
    root.withdraw()
    TestWindow(shuffled_questions, shuffle_answers_var.get())


class TestWindow(ctk.CTkToplevel):
    def __init__(self, questions, shuffle_answers):
        super().__init__()
        self.questions = questions
        self.shuffle_answers = shuffle_answers
        self.current_question = 0
        self.score = 0
        self.results = []

        self.title("Тестирование")
        self.geometry("600x400")
        self.center_window()
        self.protocol("WM_DELETE_WINDOW", self.close_test)

        self.create_widgets()
        self.show_question()

    def center_window(self):
        center_window(self, 600, 400)

    def create_widgets(self):
        self.main_frame = ctk.CTkFrame(self, corner_radius=15)
        self.main_frame.pack(expand=True, fill="both", padx=20, pady=20)

        self.question_label = ctk.CTkLabel(self.main_frame, text="", wraplength=550, justify="left", font=("Arial", 14, "bold"))
        self.question_label.pack(pady=10)

        self.options_frame = ctk.CTkFrame(self.main_frame, corner_radius=10)
        self.options_frame.pack(pady=10, fill="x")

        self.next_button = ctk.CTkButton(self.main_frame, text="Далее", command=self.next_question)
        self.next_button.pack(pady=10)

    def show_question(self):
        question = self.questions[self.current_question]
        self.question_label.configure(text=question["question"])

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
            rb = ctk.CTkRadioButton(self.options_frame, text=variant, variable=self.selected_answer, value=i, font=("Arial", 12))
            rb.pack(anchor="w", padx=20, pady=5)

    def next_question(self):
        selected_index = self.selected_answer.get()
        if selected_index == -1:
            ctk.CTkMessagebox.show_warning("Внимание", "Выберите ответ!")
            return

        is_correct = (selected_index == self.correct_index)
        self.results.append({
            "question": self.questions[self.current_question]["question"],
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
        results_window = ctk.CTkToplevel(root)
        results_window.title("Детали теста")
        results_window.geometry("700x500")
        self.center_results_window(results_window)

        results_frame = ctk.CTkFrame(results_window, corner_radius=15)
        results_frame.pack(expand=True, fill="both", padx=20, pady=20)

        title_label = ctk.CTkLabel(results_frame, text="Результаты теста", font=("Arial", 18, "bold"))
        title_label.pack(pady=(10, 20))

        results_text = ctk.CTkTextbox(results_frame, wrap="word")
        results_text.pack(expand=True, fill="both", padx=10, pady=10)
        results_text.configure(font=("Arial", 12))

        # Настраиваем теги
        results_text.tag_config("question", foreground="#000000", underline=1)
        results_text.tag_config("selected", foreground="#555555")
        results_text.tag_config("correct", foreground="#2E8B57")
        results_text.tag_config("correct_info", foreground="#008000")
        results_text.tag_config("wrong_info", foreground="#B22222")
        results_text.tag_config("separator", foreground="#888888")

        correct_count = sum(r['is_correct'] for r in self.results)
        total_count = len(self.results)
        percentage = (correct_count / total_count) * 100 if total_count > 0 else 0

        for i, result in enumerate(self.results):
            results_text.insert("end", f"Вопрос {i + 1}: {result['question']}\n", "question")
            results_text.insert("end", f"    Выбранный ответ: {result['selected']}\n", "selected")
            results_text.insert("end", f"    Правильный ответ: {result['correct']}\n", "correct")
            if result['is_correct']:
                results_text.insert("end", "    Правильно!\n", "correct_info")
            else:
                results_text.insert("end", "    Неправильно!\n", "wrong_info")

            if i < len(self.results) - 1:
                results_text.insert("end", "\n" + "-" * 50 + "\n\n", "separator")
            else:
                results_text.insert("end", "\n")

        # Итоги по процентам
        results_text.insert("end", f"\nВы ответили правильно на {correct_count} из {total_count} вопросов ({percentage:.2f}%)\n")
        results_text.configure(state="disabled")

        close_button = ctk.CTkButton(results_frame, text="Закрыть",
                                     command=lambda: self.close_results_window(results_window))
        close_button.pack(pady=10)

    def center_results_window(self, window):
        center_window(window, 700, 500)

    def close_results_window(self, results_window):
        results_window.destroy()
        root.deiconify()
        self.destroy()

    def close_test(self):
        root.deiconify()
        self.destroy()


# Главное окно
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
