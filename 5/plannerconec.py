import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta
import calendar
import winsound
import threading
import time
from base import Database 

class ModernPlanner:
    def __init__(self, root):
        self.root = root
        self.root.title("Генератор расписания дня")
        self.root.geometry("1000x600")
        self.setup_style()
    
        self.db = Database()
        
        self.selected_date = datetime.now().strftime('%Y-%m-%d')
        self.start_time = "09:00"  
        self.notification_sound = True  
        self.active_notification = None  
        self.sound_thread = None  
        self.sound_flag = False  
        
        self.create_widgets()
        self.update_task_list()
        
        self.notification_thread = threading.Thread(target=self.check_notifications, daemon=True)
        self.notification_thread.start()
    
    def setup_style(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TFrame', background='#f0f0f0')
        style.configure('TLabel', background='#f0f0f0', font=('Helvetica', 10))
        style.configure('TButton', font=('Helvetica', 10), padding=5)
        style.configure('Header.TLabel', font=('Helvetica', 12, 'bold'))
        style.map('TButton', background=[('active', '#e0e0f0')])
        
        self.priority_colors = {
            "Высокий": "#ffcccc",
            "Средний": "#ffffcc",
            "Низкий": "#ccffcc"
        }
    
    def create_widgets(self):
        header_frame = ttk.Frame(self.root)
        header_frame.pack(fill=tk.X, padx=10, pady=10)
        
        date_frame = ttk.Frame(self.root)
        date_frame.pack(fill=tk.X, padx=10, pady=5)
        
        input_frame = ttk.Frame(self.root)
        input_frame.pack(fill=tk.X, padx=10, pady=5)
        
        button_frame = ttk.Frame(self.root)
        button_frame.pack(fill=tk.X, padx=10, pady=5)
        
        table_frame = ttk.Frame(self.root)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        ttk.Label(header_frame, text="Генератор расписания дня", style='Header.TLabel').pack()
    
        ttk.Label(date_frame, text="Дата (ГГГГ-ММ-ДД):").pack(side=tk.LEFT, padx=5)
        self.date_entry = ttk.Entry(date_frame, width=15)
        self.date_entry.pack(side=tk.LEFT, padx=5)
        self.date_entry.insert(0, self.selected_date)
        self.date_entry.bind("<FocusOut>", lambda e: self.select_date_manually())
        
        ttk.Label(date_frame, text="Начало дня (ЧЧ:ММ):").pack(side=tk.LEFT, padx=5)
        self.start_time_entry = ttk.Entry(date_frame, width=5)
        self.start_time_entry.pack(side=tk.LEFT, padx=5)
        self.start_time_entry.insert(0, self.start_time)
        self.start_time_entry.bind("<FocusOut>", lambda e: self.validate_start_time())

        ttk.Button(button_frame, text="Добавить", command=self.add_task).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="Редактировать", command=self.edit_task).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="Удалить", command=self.delete_task).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="Очистить все", command=self.clear_all).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="Календарь", command=self.show_calendar).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="Сгенерировать", command=self.generate_schedule).pack(side=tk.RIGHT, padx=2)
        ttk.Button(button_frame, text="Показать расписание", command=self.show_day_schedule).pack(side=tk.RIGHT, padx=2)

        self.sound_btn = ttk.Button(button_frame, text="🔔 Звук Вкл", command=self.toggle_sound)
        self.sound_btn.pack(side=tk.RIGHT, padx=5)
    
        ttk.Label(input_frame, text="Название задачи:").grid(row=0, column=0, sticky='e', padx=5, pady=2)
        self.task_entry = ttk.Entry(input_frame, width=40)
        self.task_entry.grid(row=0, column=1, padx=5, pady=2)
        
        ttk.Label(input_frame, text="Приоритет:").grid(row=1, column=0, sticky='e', padx=5, pady=2)
        self.priority_var = tk.StringVar()
        self.priority_combo = ttk.Combobox(
            input_frame, 
            textvariable=self.priority_var,
            values=["Высокий", "Средний", "Низкий"],
            state="readonly",
            width=37
        )
        self.priority_combo.grid(row=1, column=1, padx=5, pady=2)
        self.priority_combo.current(1)
        
        ttk.Label(input_frame, text="Длительность (мин):").grid(row=2, column=0, sticky='e', padx=5, pady=2)
        self.duration_entry = ttk.Entry(input_frame, width=10)
        self.duration_entry.grid(row=2, column=1, sticky='w', padx=5, pady=2)

        self.tree = ttk.Treeview(
            table_frame,
            columns=('id', 'name', 'priority', 'duration'),
            show='headings',
            selectmode='browse'
        )
        
        self.tree.heading('id', text='ID', anchor='w')
        self.tree.heading('name', text='Название задачи')
        self.tree.heading('priority', text='Приоритет')
        self.tree.heading('duration', text='Длительность (мин)')
        
        self.tree.column('id', width=0, stretch=tk.NO)  
        self.tree.column('name', width=400, anchor='w')
        self.tree.column('priority', width=200, anchor='center')
        self.tree.column('duration', width=200, anchor='center')
        
        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.pack(fill=tk.BOTH, expand=True)
        
        self.tree.bind('<Double-1>', self.on_double_click)
    
    def update_task_list(self):
        self.tree.delete(*self.tree.get_children())
        tasks = self.db.get_tasks_by_date(self.selected_date)
        for task in tasks:
            self.tree.insert(
                '',
                tk.END,
                values=(task['id'], task['name'], task['priority'], task['duration'])
            )
    
    def add_task(self):
        self.select_date_manually()
        
        if not self.validate_input():
            return
            
        try:
            duration = int(self.duration_entry.get())
        except ValueError:
            messagebox.showwarning("Ошибка", "Длительность должна быть числом")
            return
            
        if not self.check_total_duration(duration):
            messagebox.showwarning("Ошибка", "Общая длительность задач не может превышать 24 часа (1440 минут)")
            return
            
        if not self.check_time_limit(duration):
            messagebox.showwarning("Ошибка", "Расписание выходит за пределы дня (после 23:59)")
            return
            
        self.db.add_task(
            name=self.task_entry.get(),
            priority=self.priority_var.get(),
            duration=duration,
            date=self.selected_date
        )
        
        self.update_task_list()
        self.clear_inputs()
        messagebox.showinfo("Успех", "Задача успешно добавлена!")
        self.play_notification_sound()
    
    def edit_task(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Ошибка", "Выберите задачу для редактирования")
            return
            
        item = self.tree.item(selected[0])
        task_id = item['values'][0]
        task = self.db.get_task_by_id(task_id)
        
        if not task:
            messagebox.showerror("Ошибка", "Задача не найдена")
            return
            
        edit_dialog = tk.Toplevel(self.root)
        edit_dialog.title("Редактирование задачи")
        edit_dialog.resizable(False, False)
        
        ttk.Label(edit_dialog, text="Название задачи:").grid(row=0, column=0, padx=5, pady=5, sticky='e')
        name_entry = ttk.Entry(edit_dialog, width=30)
        name_entry.grid(row=0, column=1, padx=5, pady=5)
        name_entry.insert(0, task['name'])
        
        ttk.Label(edit_dialog, text="Приоритет:").grid(row=1, column=0, padx=5, pady=5, sticky='e')
        priority_var = tk.StringVar(value=task['priority'])
        priority_combo = ttk.Combobox(
            edit_dialog,
            textvariable=priority_var,
            values=["Высокий", "Средний", "Низкий"],
            state="readonly",
            width=27
        )
        priority_combo.grid(row=1, column=1, padx=5, pady=5)
        
        ttk.Label(edit_dialog, text="Длительность (мин):").grid(row=2, column=0, padx=5, pady=5, sticky='e')
        duration_entry = ttk.Entry(edit_dialog, width=10)
        duration_entry.grid(row=2, column=1, padx=5, pady=5, sticky='w')
        duration_entry.insert(0, str(task['duration']))
        
        ttk.Label(edit_dialog, text="Дата (ГГГГ-ММ-ДД):").grid(row=3, column=0, padx=5, pady=5, sticky='e')
        date_entry = ttk.Entry(edit_dialog, width=15)
        date_entry.grid(row=3, column=1, padx=5, pady=5, sticky='w')
        date_entry.insert(0, task['date'])
        
        def save_changes():
            try:
                new_duration = int(duration_entry.get())
            except ValueError:
                messagebox.showwarning("Ошибка", "Длительность должна быть числом")
                return
            
            tasks = self.db.get_tasks_by_date(self.selected_date)
            current_total = sum(t['duration'] for t in tasks if t['id'] != task_id)
            if (current_total + new_duration) > 1440:
                messagebox.showwarning("Ошибка", "Общая длительность задач не может превышать 24 часа (1440 минут)")
                return

            if not self.check_time_limit(new_duration - task['duration']):
                messagebox.showwarning("Ошибка", "Расписание выходит за пределы дня (после 23:59)")
                return
            
            self.db.update_task(
                task_id=task_id,
                name=name_entry.get(),
                priority=priority_var.get(),
                duration=new_duration,
                date=date_entry.get()
            )
            
            self.selected_date = date_entry.get()
            self.date_entry.delete(0, tk.END)
            self.date_entry.insert(0, self.selected_date)
            
            self.update_task_list()
            edit_dialog.destroy()
            messagebox.showinfo("Успех", "Задача успешно обновлена!")
            self.play_notification_sound()
        
        def delete_task():
            if messagebox.askyesno("Подтверждение", "Вы действительно хотите удалить эту задачу?"):
                self.db.delete_task(task_id)
                self.update_task_list()
                edit_dialog.destroy()
                messagebox.showinfo("Удалено", "Задача удалена")
                self.play_notification_sound()
        
        btn_frame = ttk.Frame(edit_dialog)
        btn_frame.grid(row=4, columnspan=2, pady=10)
        
        ttk.Button(btn_frame, text="Сохранить", command=save_changes).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Удалить", command=delete_task).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Отмена", command=edit_dialog.destroy).pack(side=tk.LEFT, padx=5)
    
    def on_double_click(self, event):
        self.edit_task()
    
    def delete_task(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Ошибка", "Выберите задачу для удаления")
            return
            
        item = self.tree.item(selected[0])
        task_id = item['values'][0]
        
        if messagebox.askyesno("Подтверждение", "Вы действительно хотите удалить выбранную задачу?"):
            self.db.delete_task(task_id)
            self.update_task_list()
            messagebox.showinfo("Удалено", "Задача удалена")
            self.play_notification_sound()
    
    def clear_all(self):
        if not messagebox.askyesno("Подтверждение", "Вы действительно хотите удалить все задачи на выбранную дату?"):
            return
            
        tasks = self.db.get_tasks_by_date(self.selected_date)
        for task in tasks:
            self.db.delete_task(task['id'])
            
        self.update_task_list()
        messagebox.showinfo("Успех", "Все задачи удалены")
        self.play_notification_sound()

    def generate_schedule(self):
        try:
            date_tasks = self.db.get_tasks_by_date(self.selected_date)
            
            if not date_tasks:
                messagebox.showwarning("Ошибка", f"Нет задач на выбранную дату {self.selected_date}")
                return
                
            priority_order = {"Высокий": 1, "Средний": 2, "Низкий": 3}
            sorted_tasks = sorted(date_tasks, key=lambda x: priority_order[x['priority']])
            
            try:
                current_time = datetime.strptime(self.start_time, "%H:%M")
            except ValueError:
                current_time = datetime.strptime("09:00", "%H:%M")
            
            schedule = f"=== Расписание на {self.selected_date} ===\n\n"
            schedule += f"Начало дня: {current_time.strftime('%H:%M')}\n\n"
            
            for task in sorted_tasks:
                duration = timedelta(minutes=task['duration'])
                end_time = current_time + duration
                
                if end_time.hour >= 24:
                    messagebox.showwarning("Ошибка", "Расписание выходит за пределы дня (после 23:59)")
                    return
                
                schedule += f"{current_time.strftime('%H:%M')} - {end_time.strftime('%H:%M')}\n"
                schedule += f"  • {task['name']}\n"
                schedule += f"  • Приоритет: {task['priority']}\n"
                schedule += f"  • Длительность: {task['duration']} мин\n\n"
                
                current_time = end_time + timedelta(minutes=10)
            
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
            
            self.play_notification_sound()
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Произошла ошибка при генерации расписания: {str(e)}")
    
    def toggle_sound(self):
        self.notification_sound = not self.notification_sound
        if self.notification_sound:
            self.sound_btn.config(text="🔔 Звук Вкл")
        else:
            self.sound_btn.config(text="🔕 Звук Выкл")
            self.stop_sound()
    
    def play_continuous_sound(self):
        self.sound_flag = True
        while self.sound_flag and self.notification_sound:
            try:
                winsound.Beep(1000, 500) 
                time.sleep(0.5) 
            except:
                break
    
    def stop_sound(self):
        self.sound_flag = False
        if self.sound_thread and self.sound_thread.is_alive():
            self.sound_thread.join()
    
    def show_notification(self, title, message):
        if self.active_notification:
            self.active_notification.destroy()
        
        self.stop_sound()
        
        notification = tk.Toplevel(self.root)
        notification.title(title)
        notification.geometry("400x200")
        notification.resizable(False, False)
        notification.grab_set()  
        
        ttk.Label(notification, text=message, font=('Helvetica', 12), wraplength=380).pack(pady=20, padx=10)
        
        close_btn = ttk.Button(notification, text="Закрыть", command=lambda: self.close_notification(notification))
        close_btn.pack(pady=10)
        
        self.active_notification = notification
        
        if self.notification_sound:
            self.sound_thread = threading.Thread(target=self.play_continuous_sound, daemon=True)
            self.sound_thread.start()
    
    def close_notification(self, notification):
        self.stop_sound()
        notification.destroy()
        if notification == self.active_notification:
            self.active_notification = None
    
    def check_notifications(self):
        while True:
            now = datetime.now()
            current_time = now.strftime("%H:%M")
            current_date = now.strftime("%Y-%m-%d")
            
            tasks = self.db.get_tasks_by_date(current_date)
            if tasks:
                try:
                    start_time = datetime.strptime(self.start_time, "%H:%M")
                except ValueError:
                    start_time = datetime.strptime("09:00", "%H:%M")
                
                current_datetime = datetime.strptime(current_time, "%H:%M")
                current_total_minutes = current_datetime.hour * 60 + current_datetime.minute
                
                for task in tasks:
                    task_start = start_time
                    task_end = task_start + timedelta(minutes=task['duration'])
                    
                    reminder_time = task_start - timedelta(minutes=5)
                    reminder_minutes = reminder_time.hour * 60 + reminder_time.minute
                    
                    task_start_minutes = task_start.hour * 60 + task_start.minute
                    
                    if current_total_minutes == reminder_minutes:
                        self.show_notification(
                            "Напоминание", 
                            f"Через 5 минут начинается задача: {task['name']}\n"
                            f"Время: {task_start.strftime('%H:%M')} - {task_end.strftime('%H:%M')}\n"
                            f"Приоритет: {task['priority']}"
                        )
                    elif current_total_minutes == task_start_minutes:
                        self.show_notification(
                            "Начало задачи", 
                            f"Сейчас начинается задача: {task['name']}\n"
                            f"Время: {task_start.strftime('%H:%M')} - {task_end.strftime('%H:%M')}\n"
                            f"Приоритет: {task['priority']}"
                        )
                    
                    start_time = task_end + timedelta(minutes=10)
            
            time.sleep(30) 
    
    def validate_start_time(self):
        time_str = self.start_time_entry.get()
        try:
            datetime.strptime(time_str, '%H:%M')
            self.start_time = time_str
        except ValueError:
            messagebox.showerror("Ошибка", "Неверный формат времени. Используйте ЧЧ:ММ")
            self.start_time_entry.delete(0, tk.END)
            self.start_time_entry.insert(0, self.start_time)
    
    def check_total_duration(self, new_duration=0):
        tasks = self.db.get_tasks_by_date(self.selected_date)
        total = sum(task['duration'] for task in tasks)
        return (total + new_duration) <= 1440 
    
    def check_time_limit(self, new_duration=0):
        tasks = self.db.get_tasks_by_date(self.selected_date)
        
        try:
            start_time = datetime.strptime(self.start_time, "%H:%M")
        except ValueError:
            start_time = datetime.strptime("09:00", "%H:%M")
        
        total_duration = sum(task['duration'] for task in tasks) + new_duration
        total_minutes = (start_time.hour * 60 + start_time.minute) + total_duration + (len(tasks) * 10) 
        
        return total_minutes <= 1440 
    
    def select_date_manually(self, event=None):
        date_str = self.date_entry.get()
        try:
            datetime.strptime(date_str, '%Y-%m-%d')
            self.selected_date = date_str
            self.update_task_list()
        except ValueError:
            messagebox.showerror("Ошибка", "Неверный формат даты. Используйте ГГГГ-ММ-ДД")
            self.date_entry.delete(0, tk.END)
            self.date_entry.insert(0, self.selected_date)
    
    def show_day_schedule(self, date_str=None):
        if date_str is None:
            date_str = self.selected_date
        
        day_window = tk.Toplevel(self.root)
        day_window.title(f"Расписание на {date_str}")
        day_window.geometry("800x500")

        control_frame = ttk.Frame(day_window)
        control_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(control_frame, text="Тест звука", command=lambda: self.show_notification("Тест", "Это тестовое уведомление")).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Закрыть", command=day_window.destroy).pack(side=tk.RIGHT, padx=5)

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

        date_tasks = self.db.get_tasks_by_date(date_str)
        
        if not date_tasks:
            messagebox.showinfo("Информация", f"Нет задач на выбранную дату {date_str}")
            day_window.destroy()
            return
        
        priority_order = {"Высокий": 1, "Средний": 2, "Низкий": 3}
        sorted_tasks = sorted(date_tasks, key=lambda x: priority_order[x['priority']])
        
        try:
            current_time = datetime.strptime(self.start_time, "%H:%M")
        except ValueError:
            current_time = datetime.strptime("09:00", "%H:%M")
        
        for task in sorted_tasks:
            duration = timedelta(minutes=task['duration'])
            end_time = current_time + duration
            
            if end_time.hour == 0 and end_time.minute == 0:
                end_time_str = "00:00"
            elif end_time.hour >= 24:
                messagebox.showwarning("Ошибка", "Расписание выходит за пределы дня (после 23:59)")
                day_window.destroy()
                return
            
            time_str = f"{current_time.strftime('%H:%M')} - {end_time.strftime('%H:%M')}"
            
            schedule_tree.insert("", "end", values=(
                time_str,
                task['name'],
                task['priority'],
                task['duration']
            ))
            
            current_time = end_time + timedelta(minutes=10)
    
    def validate_input(self):
        if not self.task_entry.get():
            messagebox.showwarning("Ошибка", "Введите название задачи")
            return False
            
        if not self.duration_entry.get().isdigit():
            messagebox.showwarning("Ошибка", "Длительность должна быть числом")
            return False
            
        if int(self.duration_entry.get()) <= 0:
            messagebox.showwarning("Ошибка", "Длительность должна быть положительным числом")
            return False
            
        return True
    
    def clear_inputs(self):
        self.task_entry.delete(0, tk.END)
        self.duration_entry.delete(0, tk.END)
        self.priority_combo.current(1)
    
    def show_calendar(self):
        calendar_window = tk.Toplevel(self.root)
        calendar_window.title("Календарь")
        calendar_window.geometry("600x400")
        
        ttk.Label(calendar_window, text="Календарь", style='Header.TLabel').pack(pady=10)

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
                day_tasks = self.db.get_tasks_by_date(date_str)
                has_tasks = len(day_tasks) > 0
                
                bg_color = "#ffffff"
                if has_tasks:
                    priorities = [task['priority'] for task in day_tasks]
                    if "Высокий" in priorities:
                        bg_color = "#ffcccc"
                    elif "Средний" in priorities:
                        bg_color = "#ffffcc"
                    else:
                        bg_color = "#ccffcc"
                
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
                
                if has_tasks:
                    tooltip_text = "\n".join([f"• {task['name']}" for task in day_tasks[:3]])
                    if len(day_tasks) > 3:
                        tooltip_text += f"\n+{len(day_tasks)-3} ещё..."
                    self.create_tooltip(day_label, tooltip_text)
                
                day_label.bind("<Double-1>", lambda e, d=day: self.on_day_double_click(year, month, d, window))
                
                day_label.bind("<Button-1>", lambda e, d=day: self.on_day_click(year, month, d))

        for col in range(len(headers)):
            self.calendar_frame.grid_columnconfigure(col, weight=1, uniform="cal_col")
        for row in range(len(month_calendar) + 1):
            self.calendar_frame.grid_rowconfigure(row, weight=1, uniform="cal_row")

    def on_day_click(self, year, month, day):
        self.selected_date = f"{year:04d}-{month:02d}-{day:02d}"
        self.date_entry.delete(0, tk.END)
        self.date_entry.insert(0, self.selected_date)
        self.update_task_list()

    def on_day_double_click(self, year, month, day, parent_window):
        date_str = f"{year:04d}-{month:02d}-{day:02d}"
        parent_window.destroy()
        self.show_day_schedule(date_str)

    def create_tooltip(self, widget, text):
        tooltip = tk.Toplevel(widget)
        tooltip.wm_overrideredirect(True)
        tooltip.wm_geometry("+0+0")
        tooltip.withdraw()
        
        label = ttk.Label(
            tooltip, 
            text=text, 
            background="#ffffe0", 
            relief="solid", 
            borderwidth=1,
            padding=5,
            font=('Helvetica', 9)
        )
        label.pack()
        
        def enter(event):
            x = widget.winfo_rootx() + widget.winfo_width() + 5
            y = widget.winfo_rooty()
            tooltip.wm_geometry(f"+{x}+{y}")
            tooltip.deiconify()
        
        def leave(event):
            tooltip.withdraw()
        
        widget.bind("<Enter>", enter)
        widget.bind("<Leave>", leave)
        widget.bind("<ButtonPress>", lambda e: tooltip.withdraw())

    def play_notification_sound(self):
        if self.notification_sound:
            try:
                winsound.Beep(1000, 200)
            except:
                pass

if __name__ == "__main__":
    root = tk.Tk()
    app = ModernPlanner(root)
    root.mainloop()