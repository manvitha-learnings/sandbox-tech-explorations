import customtkinter
from datetime import datetime, timedelta
import tkcalendar
import database
import achievements
from tkinter import messagebox

# Set default theme and colors
customtkinter.set_appearance_mode("Dark")
customtkinter.set_default_color_theme("blue")

class ToDoApp(customtkinter.CTk):
    def __init__(self):
        super().__init__()
        
        # Configure window
        self.title("Done & Dusted - To-Do & Achievements Tracker")
        self.geometry("1200x750")
        self.minsize(1050, 650)
        
        # Current state
        self.selected_date = datetime.now().date()
        
        # Initialize Database
        database.init_db()
        
        # Grid layout: 3 columns (Sidebar, Tasks, Achievements)
        self.grid_columnconfigure(0, weight=0) # Sidebar: fixed width
        self.grid_columnconfigure(1, weight=3) # Tasks: large weight
        self.grid_columnconfigure(2, weight=3) # Achievements: large weight
        self.grid_rowconfigure(0, weight=1)
        
        # Create UI components
        self.create_sidebar()
        self.create_tasks_panel()
        self.create_achievements_panel()
        
        # Initial load
        self.refresh_ui()

    # --- UI Creation ---
    
    def create_sidebar(self):
        # Sidebar Frame
        self.sidebar = customtkinter.CTkFrame(self, width=260, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
        self.sidebar.grid_rowconfigure(5, weight=1) # spacer
        
        # Logo Label
        self.logo_label = customtkinter.CTkLabel(
            self.sidebar, 
            text="🎯 Done & Dusted", 
            font=customtkinter.CTkFont(family="Helvetica", size=22, weight="bold")
        )
        self.logo_label.grid(row=0, column=0, padx=20, pady=(30, 20))
        
        # Streak Card Frame
        self.streak_card = customtkinter.CTkFrame(self.sidebar, fg_color=("#FDF2E9", "#2C1D11"))
        self.streak_card.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        
        self.streak_lbl = customtkinter.CTkLabel(
            self.streak_card, 
            text="🔥 Streak: 0 Days", 
            font=customtkinter.CTkFont(size=16, weight="bold"),
            text_color="#F39C12"
        )
        self.streak_lbl.pack(pady=(10, 2))
        
        self.max_streak_lbl = customtkinter.CTkLabel(
            self.streak_card, 
            text="🏆 Max Streak: 0 Days", 
            font=customtkinter.CTkFont(size=12),
            text_color="#BDC3C7"
        )
        self.max_streak_lbl.pack(pady=(0, 10))
        
        # Date Display
        self.date_label = customtkinter.CTkLabel(
            self.sidebar, 
            text="Selected Date:\nToday", 
            font=customtkinter.CTkFont(size=14, weight="bold"),
            justify="center"
        )
        self.date_label.grid(row=2, column=0, padx=20, pady=20)
        
        # Navigation Buttons
        self.today_btn = customtkinter.CTkButton(
            self.sidebar, text="📅 Today", command=self.select_today, height=36
        )
        self.today_btn.grid(row=3, column=0, padx=20, pady=8, sticky="ew")
        
        self.tomorrow_btn = customtkinter.CTkButton(
            self.sidebar, text="🌅 Tomorrow", command=self.select_tomorrow, height=36
        )
        self.tomorrow_btn.grid(row=4, column=0, padx=20, pady=8, sticky="ew")
        
        self.calendar_btn = customtkinter.CTkButton(
            self.sidebar, text="🗓️ Select Date...", command=self.open_calendar_dialog, height=36
        )
        self.calendar_btn.grid(row=5, column=0, padx=20, pady=8, sticky="ew")
        
        # Appearance Mode Dropdown (Dark/Light)
        self.appearance_label = customtkinter.CTkLabel(self.sidebar, text="Appearance Mode:", anchor="w")
        self.appearance_label.grid(row=6, column=0, padx=20, pady=(20, 5), sticky="w")
        
        self.appearance_option = customtkinter.CTkOptionMenu(
            self.sidebar, values=["Dark", "Light", "System"], command=self.change_appearance_mode
        )
        self.appearance_option.grid(row=7, column=0, padx=20, pady=(0, 30), sticky="ew")

    def create_tasks_panel(self):
        # Tasks Frame
        self.tasks_panel = customtkinter.CTkFrame(self)
        self.tasks_panel.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        
        # Layout inside tasks panel
        self.tasks_panel.grid_rowconfigure(2, weight=1)
        self.tasks_panel.grid_columnconfigure(0, weight=1)
        
        # Header
        self.tasks_header = customtkinter.CTkLabel(
            self.tasks_panel, 
            text="Daily Tasks", 
            font=customtkinter.CTkFont(size=20, weight="bold")
        )
        self.tasks_header.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="w")
        
        # Task Input Frame
        self.task_input_frame = customtkinter.CTkFrame(self.tasks_panel, fg_color="transparent")
        self.task_input_frame.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        self.task_input_frame.grid_columnconfigure(0, weight=1)
        
        self.task_entry = customtkinter.CTkEntry(
            self.task_input_frame, 
            placeholder_text="Add a new task...", 
            height=36
        )
        self.task_entry.grid(row=0, column=0, padx=(0, 10), sticky="ew")
        self.task_entry.bind("<Return>", lambda e: self.add_task())
        
        self.priority_menu = customtkinter.CTkOptionMenu(
            self.task_input_frame, 
            values=["Low", "Medium", "High"],
            width=100,
            height=36
        )
        self.priority_menu.set("Medium")
        self.priority_menu.grid(row=0, column=1, padx=(0, 10), sticky="ew")
        
        self.task_add_btn = customtkinter.CTkButton(
            self.task_input_frame, 
            text="＋", 
            width=40,
            height=36,
            font=customtkinter.CTkFont(size=18, weight="bold"),
            command=self.add_task
        )
        self.task_add_btn.grid(row=0, column=2, sticky="ew")
        
        # Scrollable Tasks List Frame
        self.tasks_list_frame = customtkinter.CTkScrollableFrame(self.tasks_panel)
        self.tasks_list_frame.grid(row=2, column=0, padx=20, pady=(10, 20), sticky="nsew")

    def create_achievements_panel(self):
        # Achievements Frame
        self.achievements_panel = customtkinter.CTkFrame(self)
        self.achievements_panel.grid(row=0, column=2, sticky="nsew", padx=10, pady=10)
        
        # Layout inside achievements panel: Split into Logged Achievements (top) and Unlocked Badges (bottom)
        self.achievements_panel.grid_rowconfigure(2, weight=2) # Achievements list
        self.achievements_panel.grid_rowconfigure(4, weight=1) # Badges list
        self.achievements_panel.grid_columnconfigure(0, weight=1)
        
        # Header for Achievements
        self.achievements_header = customtkinter.CTkLabel(
            self.achievements_panel, 
            text="Achievements Log", 
            font=customtkinter.CTkFont(size=20, weight="bold")
        )
        self.achievements_header.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="w")
        
        # Achievement Input Frame
        self.ach_input_frame = customtkinter.CTkFrame(self.achievements_panel, fg_color="transparent")
        self.ach_input_frame.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        self.ach_input_frame.grid_columnconfigure(0, weight=1)
        
        self.ach_entry = customtkinter.CTkEntry(
            self.ach_input_frame, 
            placeholder_text="Log something you achieved today...", 
            height=36
        )
        self.ach_entry.grid(row=0, column=0, padx=(0, 10), sticky="ew")
        self.ach_entry.bind("<Return>", lambda e: self.log_manual_achievement())
        
        self.ach_add_btn = customtkinter.CTkButton(
            self.ach_input_frame, 
            text="⭐ Log", 
            width=70,
            height=36,
            command=self.log_manual_achievement
        )
        self.ach_add_btn.grid(row=0, column=1, sticky="ew")
        
        # Achievements List Frame
        self.ach_list_frame = customtkinter.CTkScrollableFrame(self.achievements_panel)
        self.ach_list_frame.grid(row=2, column=0, padx=20, pady=10, sticky="nsew")
        
        # Badges Header
        self.badges_header = customtkinter.CTkLabel(
            self.achievements_panel, 
            text="🏆 Unlocked Badges", 
            font=customtkinter.CTkFont(size=16, weight="bold")
        )
        self.badges_header.grid(row=3, column=0, padx=20, pady=(15, 5), sticky="w")
        
        # Badges Scrollable List
        self.badges_list_frame = customtkinter.CTkScrollableFrame(self.achievements_panel, height=180)
        self.badges_list_frame.grid(row=4, column=0, padx=20, pady=(5, 20), sticky="nsew")

    # --- Navigation Logic ---
    
    def select_today(self):
        self.selected_date = datetime.now().date()
        self.refresh_ui()
        
    def select_tomorrow(self):
        self.selected_date = datetime.now().date() + timedelta(days=1)
        self.refresh_ui()
        
    def open_calendar_dialog(self):
        # Open Toplevel dialog for date picker
        cal_window = customtkinter.CTkToplevel(self)
        cal_window.title("Select Date")
        cal_window.geometry("300x320")
        cal_window.resizable(False, False)
        cal_window.transient(self) # Keep on top of main window
        cal_window.grab_set() # Lock interactions with main window
        
        # Centering inside parent
        x = self.winfo_x() + (self.winfo_width() // 2) - 150
        y = self.winfo_y() + (self.winfo_height() // 2) - 160
        cal_window.geometry(f"+{x}+{y}")
        
        cal = tkcalendar.Calendar(
            cal_window, 
            selectmode='day', 
            date_pattern='y-mm-dd',
            cursor="hand2"
        )
        cal.pack(pady=20, padx=10, fill="both", expand=True)
        
        def on_date_select():
            selected_str = cal.get_date()
            self.selected_date = datetime.strptime(selected_str, "%Y-%m-%d").date()
            cal_window.destroy()
            self.refresh_ui()
            
        select_btn = customtkinter.CTkButton(cal_window, text="Select", command=on_date_select)
        select_btn.pack(pady=(0, 15))

    def change_appearance_mode(self, new_mode):
        customtkinter.set_appearance_mode(new_mode)

    # --- UI Refresh Logic ---
    
    def refresh_ui(self):
        # 1. Update date headers and active visual labels
        today = datetime.now().date()
        tomorrow = today + timedelta(days=1)
        
        if self.selected_date == today:
            date_text = f"Selected Date:\nToday ({self.selected_date.strftime('%b %d')})"
        elif self.selected_date == tomorrow:
            date_text = f"Selected Date:\nTomorrow ({self.selected_date.strftime('%b %d')})"
        else:
            date_text = f"Selected Date:\n{self.selected_date.strftime('%A, %b %d')}"
            
        self.date_label.configure(text=date_text)
        
        # 2. Update Streak card
        streak_stats = achievements.update_streak_and_get_stats()
        self.streak_lbl.configure(text=f"🔥 Streak: {streak_stats['current_streak']} Days")
        self.max_streak_lbl.configure(text=f"🏆 Max Streak: {streak_stats['max_streak']} Days")
        
        # 3. Refresh tasks
        self.refresh_tasks_list()
        
        # 4. Refresh achievements
        self.refresh_achievements_list()
        
        # 5. Check badges & refresh badge tray
        new_badges = achievements.check_and_unlock_badges(self.selected_date.strftime("%Y-%m-%d"))
        if new_badges:
            for b in new_badges:
                messagebox.showinfo("Badge Unlocked! 🎉", f"Congratulations! You unlocked the '{b['badge_name']}' badge:\n{b['description']}")
        
        self.refresh_badges_list()

    def refresh_tasks_list(self):
        # Clear existing items
        for widget in self.tasks_list_frame.winfo_children():
            widget.destroy()
            
        date_str = self.selected_date.strftime("%Y-%m-%d")
        tasks = database.get_tasks_by_date(date_str)
        
        if not tasks:
            empty_lbl = customtkinter.CTkLabel(
                self.tasks_list_frame, 
                text="No tasks scheduled for this day.", 
                text_color="gray"
            )
            empty_lbl.pack(pady=40)
            return
            
        for task in tasks:
            task_id = task["id"]
            title = task["title"]
            completed = task["completed"]
            priority = task["priority"]
            
            # Frame for each task
            task_frame = customtkinter.CTkFrame(self.tasks_list_frame)
            task_frame.pack(fill="x", padx=5, pady=4)
            task_frame.grid_columnconfigure(1, weight=1)
            
            # Completion Checkbox
            cb_var = customtkinter.BooleanVar(value=completed)
            cb = customtkinter.CTkCheckBox(
                task_frame, 
                text="", 
                variable=cb_var, 
                command=lambda t_id=task_id, var=cb_var: self.toggle_task(t_id, var.get()),
                width=24
            )
            cb.grid(row=0, column=0, padx=(10, 5), pady=10, sticky="w")
            
            # Priority color coding
            color_map = {"High": "#E74C3C", "Medium": "#F39C12", "Low": "#95A5A6"}
            p_color = color_map.get(priority, "gray")
            
            # Strikethrough style for completed tasks
            text_font = customtkinter.CTkFont(size=14, overstrike=completed)
            text_color = "gray" if completed else ("black", "white")
            
            title_lbl = customtkinter.CTkLabel(
                task_frame, 
                text=title, 
                font=text_font, 
                text_color=text_color, 
                anchor="w",
                justify="left",
                wraplength=220
            )
            title_lbl.grid(row=0, column=1, padx=5, pady=10, sticky="w")
            
            # Priority Tag
            p_badge = customtkinter.CTkFrame(task_frame, fg_color=p_color, height=20, width=60, corner_radius=4)
            p_badge.grid(row=0, column=2, padx=10, pady=10, sticky="e")
            p_badge.grid_propagate(False)
            
            p_lbl = customtkinter.CTkLabel(p_badge, text=priority, font=customtkinter.CTkFont(size=10, weight="bold"), text_color="white")
            p_lbl.pack(fill="both", expand=True)
            
            # Delete Button
            del_btn = customtkinter.CTkButton(
                task_frame, 
                text="🗑️", 
                width=30, 
                height=30,
                fg_color="transparent",
                hover_color=("#EAECEE", "#2C3E50"),
                command=lambda t_id=task_id: self.delete_task(t_id)
            )
            del_btn.grid(row=0, column=3, padx=(0, 10), pady=10, sticky="e")

    def refresh_achievements_list(self):
        # Clear existing items
        for widget in self.ach_list_frame.winfo_children():
            widget.destroy()
            
        date_str = self.selected_date.strftime("%Y-%m-%d")
        achievements_list = database.get_achievements_by_date(date_str)
        
        if not achievements_list:
            empty_lbl = customtkinter.CTkLabel(
                self.ach_list_frame, 
                text="No achievements logged for this day yet.", 
                text_color="gray"
            )
            empty_lbl.pack(pady=40)
            return
            
        for ach in achievements_list:
            ach_id = ach["id"]
            title = ach["title"]
            is_manual = ach["is_manual"]
            
            ach_frame = customtkinter.CTkFrame(self.ach_list_frame)
            ach_frame.pack(fill="x", padx=5, pady=4)
            ach_frame.grid_columnconfigure(1, weight=1)
            
            # Icon depending on manual vs auto
            icon_str = "⭐" if is_manual else "✅"
            icon_color = "#F1C40F" if is_manual else "#2ECC71"
            
            icon_lbl = customtkinter.CTkLabel(
                ach_frame, 
                text=icon_str, 
                font=customtkinter.CTkFont(size=16),
                text_color=icon_color
            )
            icon_lbl.grid(row=0, column=0, padx=(10, 5), pady=10, sticky="w")
            
            title_lbl = customtkinter.CTkLabel(
                ach_frame, 
                text=title, 
                font=customtkinter.CTkFont(size=13, weight="normal" if is_manual else "bold"),
                anchor="w",
                justify="left",
                wraplength=240
            )
            title_lbl.grid(row=0, column=1, padx=5, pady=10, sticky="w")
            
            # Delete Button
            del_btn = customtkinter.CTkButton(
                ach_frame, 
                text="🗑️", 
                width=30, 
                height=30,
                fg_color="transparent",
                hover_color=("#EAECEE", "#2C3E50"),
                command=lambda a_id=ach_id: self.delete_achievement(a_id)
            )
            del_btn.grid(row=0, column=2, padx=(0, 10), pady=10, sticky="e")

    def refresh_badges_list(self):
        # Clear existing items
        for widget in self.badges_list_frame.winfo_children():
            widget.destroy()
            
        unlocked_badges = database.get_unlocked_badges()
        
        if not unlocked_badges:
            empty_lbl = customtkinter.CTkLabel(
                self.badges_list_frame, 
                text="Complete tasks to unlock badges!", 
                text_color="gray"
            )
            empty_lbl.pack(pady=20)
            return
            
        for badge in unlocked_badges:
            badge_name = badge["badge_name"]
            desc = badge["description"]
            date_unlocked = badge["unlocked_at"]
            
            badge_frame = customtkinter.CTkFrame(self.badges_list_frame, fg_color=("#E8F8F5", "#0E2F1D"))
            badge_frame.pack(fill="x", padx=5, pady=3)
            badge_frame.grid_columnconfigure(0, weight=1)
            
            title_lbl = customtkinter.CTkLabel(
                badge_frame, 
                text=f"🏅 {badge_name}", 
                font=customtkinter.CTkFont(size=13, weight="bold"),
                text_color="#2ECC71",
                anchor="w"
            )
            title_lbl.grid(row=0, column=0, padx=10, pady=(5, 0), sticky="w")
            
            desc_lbl = customtkinter.CTkLabel(
                badge_frame, 
                text=desc, 
                font=customtkinter.CTkFont(size=11),
                text_color="gray",
                anchor="w",
                wraplength=300,
                justify="left"
            )
            desc_lbl.grid(row=1, column=0, padx=10, pady=(0, 2), sticky="w")
            
            date_lbl = customtkinter.CTkLabel(
                badge_frame, 
                text=f"Unlocked: {date_unlocked}", 
                font=customtkinter.CTkFont(size=9, slant="italic"),
                text_color="gray",
                anchor="e"
            )
            date_lbl.grid(row=2, column=0, padx=10, pady=(0, 5), sticky="e")

    # --- Actions / Event Handlers ---
    
    def add_task(self):
        title = self.task_entry.get().strip()
        if not title:
            return
            
        priority = self.priority_menu.get()
        date_str = self.selected_date.strftime("%Y-%m-%d")
        
        database.add_task(title, date_str, priority)
        self.task_entry.delete(0, 'end')
        self.refresh_ui()

    def toggle_task(self, task_id, completed):
        database.toggle_task_completed(task_id, completed)
        self.refresh_ui()

    def delete_task(self, task_id):
        database.delete_task(task_id)
        self.refresh_ui()

    def log_manual_achievement(self):
        title = self.ach_entry.get().strip()
        if not title:
            return
            
        date_str = self.selected_date.strftime("%Y-%m-%d")
        database.add_manual_achievement(title, date_str)
        self.ach_entry.delete(0, 'end')
        self.refresh_ui()

    def delete_achievement(self, achievement_id):
        database.delete_achievement(achievement_id)
        self.refresh_ui()

if __name__ == "__main__":
    app = ToDoApp()
    app.mainloop()
