import random
from docx import Document
import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox


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
center_window(root, 600, 400)


def close_app():
    if messagebox.askyesno("Подтверждение", "Вы действительно хотите выйти?"):
        root.destroy()

root.protocol("WM_DELETE_WINDOW", close_app)

def start_test_with_incorrect_questions():
    file_path = filedialog.askopenfilename(
        defaultextension=".docx",
        filetypes=[("Word Documents", "*.docx"), ("All Files", "*.*")],
        title="Выберите файл с вопросами для теста"
    )
    if not file_path:
        return  # Пользователь закрыл диалог

    try:
        questions = parse_questions(file_path)
        if not questions:
            raise ValueError("Файл не содержит вопросов или он неверно отформатирован.")
    except Exception as e:
        messagebox.showerror("Ошибка", f"Не удалось загрузить вопросы: {e}")
        return

    # Проверка перемешивания
    shuffle_questions = shuffle_answers_var.get()

    # Если нужно перемешивать вопросы
    if shuffle_questions:
        questions = random.sample(questions, len(questions))

    # Запуск теста с загруженными вопросами
    root.withdraw()
    TestWindow(questions, shuffle_answers_var.get(), 50)



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
        time_limit_str = time_limit_var.get().strip()
        if not time_limit_str.isdigit():
            time_limit = 50
        else:
            time_limit = int(time_limit_str)
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
    TestWindow(shuffled_questions, shuffle_answers_var.get(), time_limit)


def export_incorrect_questions_as_original_format(results):
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

    # Форматируем вопросы и варианты в оригинальном стиле
    for result in incorrect_results:
        document.add_paragraph(f"<question> {result['question']}")
        for variant in result["variants"]:
            document.add_paragraph(f"<variant> {variant}")

    # Сохраняем файл по указанному пути
    try:
        document.save(file_path)
        messagebox.showinfo("Экспорт завершен", f"Файл успешно сохранен: {file_path}")
    except Exception as e:
        messagebox.showerror("Ошибка", f"Не удалось сохранить файл: {e}")


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
    def __init__(self, questions, shuffle_answers, time_limit):
        super().__init__()
        self.questions = questions
        self.shuffle_answers = shuffle_answers
        self.current_question = 0
        self.score = 0
        self.results = []
        self.time_remaining = time_limit * 60

        self.title("Тестирование")
        self.state('zoomed')

        self.protocol("WM_DELETE_WINDOW", self.close_test)
        self.create_widgets()
        self.start_timer()
        self.show_question()

    def create_widgets(self):
        self.main_frame = ctk.CTkFrame(self, corner_radius=15)
        self.main_frame.pack(expand=True, fill="both", padx=20, pady=20)

        self.timer_label = ctk.CTkLabel(self.main_frame, text="", font=("Arial", 20, "bold"), text_color="red")
        self.timer_label.pack(pady=5, fill="x", expand=True)

        self.question_label = ctk.CTkLabel(self.main_frame, text="", wraplength=1000, justify="left",
                                           font=("Arial", 14, "bold"))
        self.question_label.pack(pady=10, fill="x", expand=True)

        self.options_frame = ctk.CTkFrame(self.main_frame, corner_radius=10)
        self.options_frame.pack(pady=10, fill="both", expand=True)

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
        self.bind("<space>", lambda event: self.show_correct_answer())


    def show_correct_answer(self):
        correct_answer = self.questions[self.current_question]["variants"][0]

        # Создаем новое окно
        answer_window = ctk.CTkToplevel(self)
        answer_window.title("Правильный ответ")
        answer_window.geometry("1000x300")
        center_window(answer_window, 1000, 300)

        # Основной фрейм с закругленными углами
        frame = ctk.CTkFrame(answer_window, corner_radius=15, fg_color="#F0F0F0")
        frame.pack(expand=True, fill="both", padx=20, pady=20)

        # Текст правильного ответа
        answer_label = ctk.CTkLabel(
            frame,
            text=correct_answer,
            font=("Arial", 18, "bold"),
            wraplength=450,
            justify="center",
            text_color="#333333"
        )
        answer_label.pack(expand=True, fill="both", padx=20, pady=40)

        def close_on_event(event=None):
            answer_window.destroy()

        answer_window.bind("<Key>", close_on_event)
        answer_window.bind("<Button-1>", close_on_event)

        answer_window.grab_set()

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
        if not self.variants:
            print(f"Ошибка: Вопрос {self.current_question + 1} не имеет вариантов ответа.")
            raise ValueError("Вопрос не имеет вариантов ответа.")

        if self.shuffle_answers:
            original_variants = self.variants[:]
            if not original_variants:  # Проверка перед доступом к элементам
                print(f"Ошибка: Список оригинальных вариантов пустой для вопроса {question['question']}.")
                raise IndexError("Список оригинальных вариантов пустой.")
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
                font=("Arial", 50)
            )
            rb.pack(side="left", padx=10, pady=10)

            textbox = ctk.CTkTextbox(
                row_frame,
                wrap="word",
                height=100,
                width=800
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

        results_window = ctk.CTkToplevel(root)
        results_window.title("Результаты теста")
        results_window.geometry("1600x900")
        center_window(results_window, 1600, 900)

        def close_results_window():
            if messagebox.askyesno("Подтверждение", "Вы действительно хотите завершить тестирование?"):
                results_window.destroy()
                root.deiconify()

        results_window.protocol("WM_DELETE_WINDOW", close_results_window)

        # Основной фрейм с тенью и закругленными углами
        results_frame = ctk.CTkFrame(
            results_window,
            corner_radius=15,
            fg_color="#ffffff"
        )
        results_frame.pack(expand=True, fill="both", padx=20, pady=20)

        # Заголовок с улучшенным стилем
        title_frame = ctk.CTkFrame(results_frame, fg_color="transparent")
        title_frame.pack(fill="x", padx=20, pady=(20, 10))

        title_label = ctk.CTkLabel(
            title_frame,
            text="Результаты теста",
            font=("Arial", 30, "bold"),
            text_color="#1a1a1a"
        )
        title_label.pack(pady=10)

        # Статистика
        correct_count = sum(r['is_correct'] for r in self.results)
        total_count = len(self.results)
        percentage = (correct_count / total_count) * 100 if total_count > 0 else 0

        stats_frame = ctk.CTkFrame(results_frame, fg_color="#f0f0f0", corner_radius=10)
        stats_frame.pack(fill="x", padx=20, pady=10)

        stats_label = ctk.CTkLabel(
            stats_frame,
            text=f"Правильных ответов: {correct_count} из {total_count} ({percentage:.1f}%)",
            font=("Arial", 24),
            text_color="#333333"
        )
        stats_label.pack(pady=15)

        # Создаем скроллируемый фрейм для результатов
        scroll_frame = ctk.CTkScrollableFrame(
            results_frame,
            fg_color="#ffffff",
            corner_radius=10
        )
        scroll_frame.pack(expand=True, fill="both", padx=20, pady=10)

        # Добавляем результаты
        for i, result in enumerate(self.results, 1):
            # Фрейм для каждого вопроса
            question_frame = ctk.CTkFrame(
                scroll_frame,
                fg_color="#f8f9fa" if result['is_correct'] else "#fff3f3",
                corner_radius=10
            )
            question_frame.pack(fill="x", padx=10, pady=5)

            # Номер вопроса
            question_number = ctk.CTkLabel(
                question_frame,
                text=f"Вопрос {i}",
                font=("Arial", 24, "bold"),
                text_color="#1a1a1a"
            )
            question_number.pack(anchor="w", padx=15, pady=(10, 5))

            # Текст вопроса
            question_text = ctk.CTkLabel(
                question_frame,
                text=result['question'],
                font=("Arial", 22),
                wraplength=1400,
                justify="left",
                text_color="#333333"
            )
            question_text.pack(anchor="w", padx=15, pady=5)

            # Ваш ответ
            answer_label = ctk.CTkLabel(
                question_frame,
                text=f"Ваш ответ: {result['selected']}",
                font=("Arial", 22),
                wraplength=1400,
                justify="left",
                text_color="#0066cc"
            )
            answer_label.pack(anchor="w", padx=15, pady=5)

            # Правильный ответ (показываем только если ответ неверный)
            if not result['is_correct']:
                correct_label = ctk.CTkLabel(
                    question_frame,
                    text=f"Правильный ответ: {result['correct']}",
                    font=("Arial", 22),
                    wraplength=1400,
                    justify="left",
                    text_color="#28a745"
                )
                correct_label.pack(anchor="w", padx=15, pady=5)

            # Статус
            status_frame = ctk.CTkFrame(
                question_frame,
                fg_color="transparent"
            )
            status_frame.pack(fill="x", padx=15, pady=(5, 10))

            status_label = ctk.CTkLabel(
                status_frame,
                text="✓ Верно" if result['is_correct'] else "✗ Неверно",
                font=("Arial", 20, "bold"),
                text_color="#28a745" if result['is_correct'] else "#dc3545"
            )
            status_label.pack(side="left")

        # Кнопки управления
        # Центрирующий контейнер для кнопок
        button_container = ctk.CTkFrame(results_frame, fg_color="transparent")
        button_container.pack(fill="x", padx=20, pady=20)

        # Внутренний фрейм для кнопок, который будет центрирован
        button_frame = ctk.CTkFrame(button_container, fg_color="transparent")
        button_frame.pack(expand=True)

        retry_all_button = ctk.CTkButton(
            button_frame,
            text="Пройти заново (все вопросы)",
            font=("Arial", 14),
            command=lambda: self.retry_with_all_questions(results_window)
        )
        retry_all_button.pack(side="left", padx=10)

        if incorrect_questions:
            retry_incorrect_button = ctk.CTkButton(
                button_frame,
                text="Пройти заново (ошибки)",
                font=("Arial", 14),
                command=lambda: self.retry_with_incorrect(incorrect_questions, results_window)
            )
            retry_incorrect_button.pack(side="left", padx=10)

            export_button = ctk.CTkButton(
                button_frame,
                text="Экспортировать неправильные ответы",
                font=("Arial", 14),
                command=lambda: export_incorrect_answers(self.results)
            )
            export_button.pack(side="left", padx=10)

            export_original_button = ctk.CTkButton(
                button_frame,
                text="Экспортировать ошибки (ориг. формат)",
                font=("Arial", 14),
                command=lambda: export_incorrect_questions_as_original_format(self.results)
            )
            export_original_button.pack(side="left", padx=10)

    def retry_with_all_questions(self, results_window):
        results_window.destroy()
        self.destroy()
        TestWindow(self.questions, self.shuffle_answers, 50)

    def retry_with_incorrect(self, incorrect_questions, results_window):
        results_window.destroy()
        self.destroy()
        TestWindow(incorrect_questions, self.shuffle_answers, 50)

    def close_results_window(self, results_window):
        if messagebox.askyesno("Подтверждение", "Вы действительно хотите завершить тестирование?"):
            results_window.destroy()
            root.deiconify()
            self.destroy()

    def close_test(self):
        if messagebox.askyesno("Подтверждение", "Вы действительно хотите завершить тестирование?"):
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

ctk.CTkLabel(input_frame, text="Время (минуты):", font=("Arial", 14)).grid(row=2, column=0, padx=10, pady=10, sticky="e")

time_limit_var = ctk.StringVar(value="50")
time_limit_entry = ctk.CTkEntry(input_frame, textvariable=time_limit_var, width=100)
time_limit_entry.grid(row=2, column=1, padx=10, pady=10)

ctk.CTkLabel(input_frame, text="Перемешивать варианты ответов?", font=("Arial", 14)).grid(row=1, column=0, padx=10, pady=10, sticky="e")

shuffle_answers_var = ctk.BooleanVar(value=True)
shuffle_checkbox = ctk.CTkCheckBox(input_frame, text="Да", variable=shuffle_answers_var)
shuffle_checkbox.grid(row=1, column=1, padx=10, pady=10)

start_button = ctk.CTkButton(main_frame, text="Начать тест", command=start_test)
start_button.pack(pady=20)


start_from_file_button = ctk.CTkButton(
    main_frame,
    text="Начать тест из файла с ошибками",
    command=start_test_with_incorrect_questions
)
start_from_file_button.pack(pady=10)


root.mainloop()