import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime, timedelta
import calendar

class IntermediatePlanner:
    def __init__(self, root):
        self.root = root
        self.root.title("Генератор расписания дня")
        self.root.geometry("900x600")
        self.conn = sqlite3.connect('planner.db')
        self.create_table()
        self.current_date = datetime.now().strftime('%Y-%m-%d')
        self.start_time = "09:00"
        self.create_widgets()
        self.load_tasks()

    def create_table(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                priority TEXT NOT NULL,
                duration INTEGER NOT NULL,
                date TEXT NOT NULL
            )
        ''')
        self.conn.commit()

    def create_widgets(self):
        header_frame = ttk.Frame(self.root)
        header_frame.pack(fill=tk.X, padx=10, pady=10)
        ttk.Label(header_frame, text="Генератор расписания дня", font=('Helvetica', 12, 'bold')).pack()
        
        date_frame = ttk.Frame(self.root)
        date_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(date_frame, text="Дата (ГГГГ-ММ-ДД):").pack(side=tk.LEFT)
        self.date_entry = ttk.Entry(date_frame, width=15)
        self.date_entry.pack(side=tk.LEFT, padx=5)
        self.date_entry.insert(0, self.current_date)
        
        ttk.Button(date_frame, text="Календарь", command=self.show_calendar).pack(side=tk.LEFT, padx=5)
        
        ttk.Label(date_frame, text="Начало дня (ЧЧ:ММ):").pack(side=tk.LEFT, padx=5)
        self.start_time_entry = ttk.Entry(date_frame, width=5)
        self.start_time_entry.pack(side=tk.LEFT, padx=5)
        self.start_time_entry.insert(0, self.start_time)
        
        input_frame = ttk.Frame(self.root)
        input_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(input_frame, text="Задача:").grid(row=0, column=0, sticky='e')
        self.task_entry = ttk.Entry(input_frame, width=40)
        self.task_entry.grid(row=0, column=1, padx=5)
        
        ttk.Label(input_frame, text="Приоритет:").grid(row=1, column=0, sticky='e')
        self.priority = ttk.Combobox(input_frame, values=["Высокий", "Средний", "Низкий"], width=37)
        self.priority.grid(row=1, column=1, padx=5)
        self.priority.current(1)
        
        ttk.Label(input_frame, text="Длительность (мин):").grid(row=2, column=0, sticky='e')
        self.duration = ttk.Entry(input_frame, width=10)
        self.duration.grid(row=2, column=1, sticky='w', padx=5)
        
        button_frame = ttk.Frame(self.root)
        button_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(button_frame, text="Добавить", command=self.add_task).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="Редактировать", command=self.edit_task).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="Удалить", command=self.delete_task).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="Очистить все", command=self.clear_all).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="Сгенерировать", command=self.generate_schedule).pack(side=tk.RIGHT, padx=2)
        ttk.Button(button_frame, text="Показать расписание", command=self.show_schedule).pack(side=tk.RIGHT, padx=2)
        
        self.tree = ttk.Treeview(
            self.root,
            columns=('id', 'name', 'priority', 'duration'),
            show='headings',
            selectmode='browse'
        )
        self.tree.heading('name', text='Название задачи')
        self.tree.heading('priority', text='Приоритет')
        self.tree.heading('duration', text='Длительность (мин)')
        self.tree.column('id', width=0, stretch=tk.NO)
        self.tree.column('name', width=400)
        self.tree.column('priority', width=200, anchor='center')
        self.tree.column('duration', width=200, anchor='center')
        
        scrollbar = ttk.Scrollbar(self.root, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.tree.bind('<Double-1>', lambda e: self.edit_task())

    def load_tasks(self):
        self.tree.delete(*self.tree.get_children())
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM tasks WHERE date=?", (self.current_date,))
        for task in cursor.fetchall():
            self.tree.insert('', 'end', values=task)

    def add_task(self):
        name = self.task_entry.get()
        priority = self.priority.get()
        duration = self.duration.get()
        date = self.date_entry.get()
        
        if not name or not duration:
            messagebox.showwarning("Ошибка", "Заполните все поля")
            return
        
        try:
            datetime.strptime(date, '%Y-%m-%d')
        except ValueError:
            messagebox.showerror("Ошибка", "Неверный формат даты. Используйте ГГГГ-ММ-ДД")
            return
        
        try:
            duration = int(duration)
            if duration <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Ошибка", "Длительность должна быть положительным числом")
            return
        
        cursor = self.conn.cursor()
        cursor.execute("SELECT SUM(duration) FROM tasks WHERE date=?", (date,))
        total = cursor.fetchone()[0] or 0
        if (total + duration) > 1440:  # 24 часа = 1440 минут
            messagebox.showwarning("Ошибка", "Общая длительность задач не может превышать 24 часа (1440 минут)")
            return
        
        cursor.execute("INSERT INTO tasks (name, priority, duration, date) VALUES (?, ?, ?, ?)",
                      (name, priority, duration, date))
        self.conn.commit()
        
        self.current_date = date
        self.load_tasks()
        self.task_entry.delete(0, tk.END)
        self.duration.delete(0, tk.END)

    def edit_task(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Ошибка", "Выберите задачу")
            return
            
        task_id = self.tree.item(selected[0])['values'][0]
        
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM tasks WHERE id=?", (task_id,))
        task = cursor.fetchone()
        
        edit_window = tk.Toplevel(self.root)
        edit_window.title("Редактировать задачу")
        edit_window.resizable(False, False)
        
        ttk.Label(edit_window, text="Задача:").grid(row=0, column=0, padx=5, pady=5, sticky='e')
        name_entry = ttk.Entry(edit_window, width=30)
        name_entry.grid(row=0, column=1, padx=5, pady=5)
        name_entry.insert(0, task[1])
        
        ttk.Label(edit_window, text="Приоритет:").grid(row=1, column=0, padx=5, pady=5, sticky='e')
        priority = ttk.Combobox(edit_window, values=["Высокий", "Средний", "Низкий"], width=27)
        priority.grid(row=1, column=1, padx=5, pady=5)
        priority.set(task[2])
        
        ttk.Label(edit_window, text="Длительность:").grid(row=2, column=0, padx=5, pady=5, sticky='e')
        duration = ttk.Entry(edit_window, width=10)
        duration.grid(row=2, column=1, padx=5, pady=5, sticky='w')
        duration.insert(0, task[3])
        
        ttk.Label(edit_window, text="Дата:").grid(row=3, column=0, padx=5, pady=5, sticky='e')
        date_entry = ttk.Entry(edit_window, width=15)
        date_entry.grid(row=3, column=1, padx=5, pady=5, sticky='w')
        date_entry.insert(0, task[4])
        
        def save_changes():
            try:
                new_duration = int(duration.get())
                if new_duration <= 0:
                    raise ValueError
            except ValueError:
                messagebox.showerror("Ошибка", "Длительность должна быть положительным числом")
                return
            
            cursor.execute("SELECT SUM(duration) FROM tasks WHERE date=? AND id!=?", (date_entry.get(), task_id))
            total = cursor.fetchone()[0] or 0
            if (total + new_duration) > 1440:
                messagebox.showwarning("Ошибка", "Общая длительность задач не может превышать 24 часа (1440 минут)")
                return
            
            cursor.execute("UPDATE tasks SET name=?, priority=?, duration=?, date=? WHERE id=?",
                         (name_entry.get(), priority.get(), new_duration, date_entry.get(), task_id))
            self.conn.commit()
            self.current_date = date_entry.get()
            self.date_entry.delete(0, tk.END)
            self.date_entry.insert(0, self.current_date)
            edit_window.destroy()
            self.load_tasks()
            
        btn_frame = ttk.Frame(edit_window)
        btn_frame.grid(row=4, columnspan=2, pady=10)
        
        ttk.Button(btn_frame, text="Сохранить", command=save_changes).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Удалить", command=lambda: self.delete_task(task_id, edit_window)).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Отмена", command=edit_window.destroy).pack(side=tk.LEFT, padx=5)

    def delete_task(self, task_id=None, window=None):
        if task_id is None:
            selected = self.tree.selection()
            if not selected:
                messagebox.showwarning("Ошибка", "Выберите задачу")
                return
            task_id = self.tree.item(selected[0])['values'][0]
            
        if messagebox.askyesno("Подтверждение", "Удалить задачу?"):
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM tasks WHERE id=?", (task_id,))
            self.conn.commit()
            self.load_tasks()
            if window:
                window.destroy()

    def clear_all(self):
        if messagebox.askyesno("Подтверждение", "Удалить ВСЕ задачи на выбранную дату?"):
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM tasks WHERE date=?", (self.current_date,))
            self.conn.commit()
            self.load_tasks()

    def generate_schedule(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM tasks WHERE date=? ORDER BY CASE priority WHEN 'Высокий' THEN 1 WHEN 'Средний' THEN 2 ELSE 3 END", 
                      (self.current_date,))
        tasks = cursor.fetchall()
        
        if not tasks:
            messagebox.showwarning("Ошибка", "Нет задач на выбранную дату")
            return
            
        try:
            start_time = self.start_time_entry.get()
            current_time = datetime.strptime(start_time, "%H:%M")
        except ValueError:
            messagebox.showerror("Ошибка", "Неверный формат времени начала. Используйте ЧЧ:ММ")
            return
        
        schedule = f"=== Расписание на {self.current_date} ===\n\n"
        schedule += f"Начало дня: {current_time.strftime('%H:%M')}\n\n"
        
        for task in tasks:
            duration = timedelta(minutes=task[3])
            end_time = current_time + duration
            
            if end_time.hour >= 24:
                messagebox.showwarning("Ошибка", "Расписание выходит за пределы дня (после 23:59)")
                return
            
            schedule += f"{current_time.strftime('%H:%M')} - {end_time.strftime('%H:%M')}\n"
            schedule += f"  • {task[1]}\n"
            schedule += f"  • Приоритет: {task[2]}\n"
            schedule += f"  • Длительность: {task[3]} мин\n\n"
            
            current_time = end_time + timedelta(minutes=10)  # Перерыв 10 минут
        
        result_window = tk.Toplevel(self.root)
        result_window.title("Сгенерированное расписание")
        result_window.geometry("500x600")
        
        text_frame = ttk.Frame(result_window)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        text = tk.Text(text_frame, wrap=tk.WORD, font=('Helvetica', 10))
        scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=text.yview)
        text.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        text.pack(fill=tk.BOTH, expand=True)
        
        text.insert(tk.END, schedule)
        text.config(state=tk.DISABLED)

    def show_schedule(self):
        self.show_day_schedule(self.current_date)

    def show_day_schedule(self, date_str):
        day_window = tk.Toplevel(self.root)
        day_window.title(f"Расписание на {date_str}")
        day_window.geometry("800x500")

        schedule_tree = ttk.Treeview(
            day_window,
            columns=("time", "task", "priority", "duration"),
            show="headings",
            height=15
        )
        
        schedule_tree.heading("time", text="Время")
        schedule_tree.heading("task", text="Название задачи")
        schedule_tree.heading("priority", text="Приоритет")
        schedule_tree.heading("duration", text="Длительность (м)")
        
        schedule_tree.column("time", width=150, anchor="center")
        schedule_tree.column("task", width=300, anchor="w")
        schedule_tree.column("priority", width=150, anchor="center")
        schedule_tree.column("duration", width=150, anchor="center")
        
        scrollbar = ttk.Scrollbar(day_window, orient=tk.VERTICAL, command=schedule_tree.yview)
        schedule_tree.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        schedule_tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM tasks WHERE date=? ORDER BY CASE priority WHEN 'Высокий' THEN 1 WHEN 'Средний' THEN 2 ELSE 3 END", 
                      (date_str,))
        tasks = cursor.fetchall()
        
        if not tasks:
            messagebox.showinfo("Информация", f"Нет задач на выбранную дату {date_str}")
            day_window.destroy()
            return
        
        try:
            start_time = self.start_time_entry.get()
            current_time = datetime.strptime(start_time, "%H:%M")
        except ValueError:
            current_time = datetime.strptime("09:00", "%H:%M")
        
        for task in tasks:
            duration = timedelta(minutes=task[3])
            end_time = current_time + duration
            
            if end_time.hour >= 24:
                messagebox.showwarning("Ошибка", "Расписание выходит за пределы дня (после 23:59)")
                day_window.destroy()
                return
            
            time_str = f"{current_time.strftime('%H:%M')} - {end_time.strftime('%H:%M')}"
            
            schedule_tree.insert("", "end", values=(
                time_str,
                task[1],
                task[2],
                task[3]
            ))
            
            current_time = end_time + timedelta(minutes=10)

    def show_calendar(self):
        calendar_window = tk.Toplevel(self.root)
        calendar_window.title("Календарь")
        calendar_window.geometry("600x400")
        
        ttk.Label(calendar_window, text="Календарь", font=('Helvetica', 12, 'bold')).pack(pady=10)

        control_frame = ttk.Frame(calendar_window)
        control_frame.pack()

        self.year_var = tk.IntVar(value=datetime.now().year)
        self.month_var = tk.IntVar(value=datetime.now().month)

        ttk.Button(control_frame, text="←", command=lambda: self.change_month(-1, calendar_window)).grid(row=0, column=0)
        self.month_label = ttk.Label(control_frame, text="", width=15, anchor="center")
        self.month_label.grid(row=0, column=1, padx=10)
        ttk.Button(control_frame, text="→", command=lambda: self.change_month(1, calendar_window)).grid(row=0, column=2)

        self.calendar_frame = ttk.Frame(calendar_window)
        self.calendar_frame.pack(pady=10)

        self.render_calendar(calendar_window)

    def change_month(self, delta, window):
        current_month = self.month_var.get()
        current_year = self.year_var.get()
        
        new_month = current_month + delta
        
        if new_month < 1:
            new_month = 12
            self.year_var.set(current_year - 1)
        elif new_month > 12:
            new_month = 1
            self.year_var.set(current_year + 1)
        
        self.month_var.set(new_month)
        self.render_calendar(window)

    def render_calendar(self, window):
        for widget in self.calendar_frame.winfo_children():
            widget.destroy()

        year = self.year_var.get()
        month = self.month_var.get()
        self.month_label.config(text=f"{calendar.month_name[month]} {year}")

        headers = ["№", "ПН", "ВТ", "СР", "ЧТ", "ПТ", "СБ", "ВС"]
        for col, header in enumerate(headers):
            ttk.Label(self.calendar_frame, text=header, borderwidth=1, relief="solid", 
                     padding=3, background="#f0f0f0", font=('Helvetica', 9, 'bold')).grid(
                     row=0, column=col, sticky="nsew", padx=1, pady=1)

        month_calendar = calendar.monthcalendar(year, month)
        
        for week_num, week in enumerate(month_calendar, start=1):
            ttk.Label(self.calendar_frame, text=str(week_num), borderwidth=1, relief="solid",
                     padding=3, background="#f0f0f0").grid(
                     row=week_num, column=0, sticky="nsew", padx=1, pady=1)
            
            for day_num, day in enumerate(week, start=1):
                if day == 0:
                    continue
                    
                date_str = f"{year:04d}-{month:02d}-{day:02d}"
                cursor = self.conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM tasks WHERE date=?", (date_str,))
                has_tasks = cursor.fetchone()[0] > 0
                
                bg_color = "#ffffcc" if has_tasks else "#ffffff"
                
                day_label = ttk.Label(
                    self.calendar_frame, 
                    text=str(day),
                    borderwidth=1,
                    relief="solid",
                    padding=3,
                    background=bg_color,
                    anchor="center"
                )
                day_label.grid(row=week_num, column=day_num, sticky="nsew", padx=1, pady=1)
        
                day_label.bind("<Double-1>", lambda e, d=day: self.on_day_double_click(year, month, d, window))
                
                day_label.bind("<Button-1>", lambda e, d=day: self.on_day_click(year, month, d))

        for col in range(len(headers)):
            self.calendar_frame.grid_columnconfigure(col, weight=1, uniform="cal_col")
        for row in range(len(month_calendar) + 1):
            self.calendar_frame.grid_rowconfigure(row, weight=1, uniform="cal_row")

    def on_day_click(self, year, month, day):
        self.current_date = f"{year:04d}-{month:02d}-{day:02d}"
        self.date_entry.delete(0, tk.END)
        self.date_entry.insert(0, self.current_date)
        self.load_tasks()

    def on_day_double_click(self, year, month, day, parent_window):
        date_str = f"{year:04d}-{month:02d}-{day:02d}"
        parent_window.destroy()
        self.show_day_schedule(date_str)

    def __del__(self):
        self.conn.close()

if __name__ == "__main__":
    root = tk.Tk()
    app = IntermediatePlanner(root)
    root.mainloop()