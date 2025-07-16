import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime, timedelta

class BasicPlanner:
    def __init__(self, root):
        self.root = root
        self.root.title("Генератор расписания дня")
        self.root.geometry("800x500")
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
        # Фрейм для ввода данных
        input_frame = ttk.Frame(self.root)
        input_frame.pack(pady=10)
        
        ttk.Label(input_frame, text="Дата (ГГГГ-ММ-ДД):").grid(row=0, column=0)
        self.date_entry = ttk.Entry(input_frame, width=15)
        self.date_entry.grid(row=0, column=1)
        self.date_entry.insert(0, self.current_date)
        
        ttk.Label(input_frame, text="Задача:").grid(row=1, column=0)
        self.task_entry = ttk.Entry(input_frame, width=30)
        self.task_entry.grid(row=1, column=1)
        
        ttk.Label(input_frame, text="Приоритет:").grid(row=2, column=0)
        self.priority = ttk.Combobox(input_frame, values=["Высокий", "Средний", "Низкий"])
        self.priority.grid(row=2, column=1)
        self.priority.current(1)
        
        ttk.Label(input_frame, text="Длительность (мин):").grid(row=3, column=0)
        self.duration = ttk.Entry(input_frame, width=10)
        self.duration.grid(row=3, column=1)
        
        # Фрейм для кнопок
        button_frame = ttk.Frame(self.root)
        button_frame.pack(pady=5)
        
        ttk.Button(button_frame, text="Добавить", command=self.add_task).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Редактировать", command=self.edit_task).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Удалить", command=self.delete_task).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Очистить все", command=self.clear_all).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Сгенерировать", command=self.generate_schedule).pack(side=tk.LEFT, padx=5)
        
        # Таблица задач
        self.tree = ttk.Treeview(self.root, columns=('id', 'name', 'priority', 'duration'), show='headings')
        self.tree.heading('name', text='Задача')
        self.tree.heading('priority', text='Приоритет')
        self.tree.heading('duration', text='Длительность')
        self.tree.column('id', width=0, stretch=tk.NO)
        self.tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

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
        
        cursor = self.conn.cursor()
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
        
        ttk.Label(edit_window, text="Задача:").grid(row=0, column=0)
        name_entry = ttk.Entry(edit_window)
        name_entry.grid(row=0, column=1)
        name_entry.insert(0, task[1])
        
        ttk.Label(edit_window, text="Приоритет:").grid(row=1, column=0)
        priority = ttk.Combobox(edit_window, values=["Высокий", "Средний", "Низкий"])
        priority.grid(row=1, column=1)
        priority.set(task[2])
        
        ttk.Label(edit_window, text="Длительность:").grid(row=2, column=0)
        duration = ttk.Entry(edit_window)
        duration.grid(row=2, column=1)
        duration.insert(0, task[3])
        
        ttk.Label(edit_window, text="Дата:").grid(row=3, column=0)
        date_entry = ttk.Entry(edit_window)
        date_entry.grid(row=3, column=1)
        date_entry.insert(0, task[4])
        
        def save_changes():
            cursor.execute("UPDATE tasks SET name=?, priority=?, duration=?, date=? WHERE id=?",
                         (name_entry.get(), priority.get(), duration.get(), date_entry.get(), task_id))
            self.conn.commit()
            self.current_date = date_entry.get()
            self.date_entry.delete(0, tk.END)
            self.date_entry.insert(0, self.current_date)
            edit_window.destroy()
            self.load_tasks()
            
        ttk.Button(edit_window, text="Сохранить", command=save_changes).grid(row=4, columnspan=2)

    def delete_task(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Ошибка", "Выберите задачу")
            return
            
        if messagebox.askyesno("Подтверждение", "Удалить задачу?"):
            task_id = self.tree.item(selected[0])['values'][0]
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM tasks WHERE id=?", (task_id,))
            self.conn.commit()
            self.load_tasks()

    def clear_all(self):
        if messagebox.askyesno("Подтверждение", "Удалить ВСЕ задачи на выбранную дату?"):
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM tasks WHERE date=?", (self.current_date,))
            self.conn.commit()
            self.load_tasks()

    def generate_schedule(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM tasks WHERE date=? ORDER BY priority", (self.current_date,))
        tasks = cursor.fetchall()
        
        if not tasks:
            messagebox.showwarning("Ошибка", "Нет задач на выбранную дату")
            return
            
        try:
            current_time = datetime.strptime(self.start_time, "%H:%M")
        except ValueError:
            current_time = datetime.strptime("09:00", "%H:%M")
        
        schedule = f"=== Расписание на {self.current_date} ===\n\n"
        schedule += f"Начало дня: {current_time.strftime('%H:%M')}\n\n"
        
        for task in tasks:
            duration = timedelta(minutes=task[3])
            end_time = current_time + duration
            
            schedule += f"{current_time.strftime('%H:%M')} - {end_time.strftime('%H:%M')}\n"
            schedule += f"  • {task[1]}\n"
            schedule += f"  • Приоритет: {task[2]}\n"
            schedule += f"  • Длительность: {task[3]} мин\n\n"
            
            current_time = end_time + timedelta(minutes=10)  # Перерыв 10 минут
        
        result_window = tk.Toplevel(self.root)
        result_window.title("Расписание")
        
        text = tk.Text(result_window, wrap=tk.WORD)
        scrollbar = ttk.Scrollbar(result_window, orient=tk.VERTICAL, command=text.yview)
        text.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        text.pack(fill=tk.BOTH, expand=True)
        
        text.insert(tk.END, schedule)
        text.config(state=tk.DISABLED)

    def __del__(self):
        self.conn.close()

if __name__ == "__main__":
    root = tk.Tk()
    app = BasicPlanner(root)
    root.mainloop()