import tkinter as tk
import datetime
import random
from tkinter import messagebox

from game.special_rooms.quarters import build_default_locker_inventory
from game.stock_market import default_stock_market_state, serialize_companies

# List of potential NPC names
NPC_NAMES = [
    "Alex Chen", "Morgan Yu", "Sarah Connor", "John Shepard", "Ellen Ripley",
    "Isaac Clarke", "Samantha Carter", "Jean-Luc Picard", "Nyota Uhura", "Malcolm Reynolds",
    "River Tam", "Kaidan Alenko", "Liara T'Soni", "James Holden", "Naomi Nagata",
    "Amos Burton", "Alex Kamal", "Camina Drummer", "Julie Mao", "Joe Miller",
    "Kara Thrace", "William Adama", "Laura Roslin", "Gaius Baltar", "Sharon Valerii",
    "David Bowman", "Frank Poole", "Chris Hadfield", "Valentina Tereshkova", "Yuri Gagarin",
    "Sally Ride", "Neil Armstrong", "Mae Jemison", "Buzz Aldrin", "Alan Shepard",
    "Jim Lovell", "John Glenn", "Peggy Whitson", "Scott Kelly", "Christina Koch",
    "Anne McClain", "Jessica Meir", "Sunita Williams", "Mark Kelly", "Michael Collins",
    "Helen Sharman", "Tim Peake", "Andreas Mogensen", "Thomas Pesquet", "Samantha Cristoforetti"
]

JOBS = {
    "Staff Assistant": {
        "department": "Civilian",
        "subdepartment": "Assistant",
        "credits": 1000,
        "description": "Staff Assistants are the backbone of daily station operations. They handle various tasks as needed across the station. Starting with 1000 credits.",
    },
    "Engineer": {
        "department": "Engineering",
        "subdepartment": "Engineer",
        "credits": 2500,
        "description": "Engineers are responsible for keeping the station's critical systems operational. They excel at repairing equipment and solving technical problems. Starting with 2500 credits and access to the Engineering Station.",
    },
    "Security Guard": {
        "department": "Security",
        "subdepartment": "Security",
        "credits": 5000,
        "description": "Security Guards maintain order and protect the station from threats. They have access to security systems and equipment. Starting with 5000 credits and access to the Security Station.",
    },
    "Doctor": {
        "department": "Medical",
        "subdepartment": "Doctor",
        "credits": 7500,
        "description": "Doctors provide medical care to the station's crew. They can diagnose and treat a variety of conditions. Starting with 7500 credits and access to the MedBay Station.",
    },
    "Captain": {
        "department": "Administration",
        "subdepartment": "Captain",
        "credits": 10000,
        "description": "The Captain is the highest authority on the station. They make critical decisions and coordinate all departments. Starting with 10000 credits and access to all station areas.",
    },
    "Bartender": {
        "department": "Civilian",
        "subdepartment": "Bar",
        "credits": 3500,
        "description": "Bartenders run the station's social hub, mixing drinks and providing a place for crew members to relax. They have deep knowledge of beverages and excellent social skills. Starting with 3500 credits and access to the Bar Station.",
    },
    "Head of Personnel": {
        "department": "Administration",
        "subdepartment": "HoP",
        "credits": 9000,
        "description": "The Head of Personnel (HoP) is the second-in-command of the station. They manage crew assignments, access permissions, and administrative matters. Starting with 9000 credits and access to the HoP Station and Bar Station.",
    },
    "Botanist": {
        "department": "Civilian",
        "subdepartment": "Botany",
        "credits": 3000,
        "description": "Botanists cultivate and maintain the station's plant life. They grow food, medicinal herbs, and decorative plants in the Botany Lab. Starting with 3000 credits and access to the Botany Station.",
    },
}


DEPARTMENT_ORDER = [
    "Civilian",
    "Medical",
    "Engineering",
    "Security",
    "Administration",
]


def group_jobs_by_department():
    """Group jobs by department, sorted by DEPARTMENT_ORDER with credits ascending within each."""
    by_dept = {}
    for job_name, job_info in JOBS.items():
        by_dept.setdefault(job_info["department"], []).append((job_name, job_info["credits"]))

    result = []
    seen = set()
    for dept in DEPARTMENT_ORDER:
        if dept in by_dept:
            jobs = sorted(by_dept[dept], key=lambda x: x[1])
            result.append((dept, [job_name for job_name, _ in jobs]))
            seen.add(dept)

    for dept in sorted(by_dept.keys()):
        if dept not in seen:
            jobs = sorted(by_dept[dept], key=lambda x: x[1])
            result.append((dept, [job_name for job_name, _ in jobs]))

    return result


SELECT_DEPARTMENT = "Select A Department"
SELECT_JOB = "Select A Job"


def get_jobs_for_department(department):
    """Return sorted job names for a department, or empty list if not found."""
    for dept, jobs in group_jobs_by_department():
        if dept == department:
            return jobs
    return []


class CharacterCreation:
    """Character creation screen rendered in the main game window.

    Builds the player's data (job, credits, permissions, station power, stock
    market state) and generates the NPC crew, then hands both back to the game
    via the on_complete callback.
    """

    def __init__(self, root, player_data, companies, on_back, on_complete):
        self.root = root
        self.player_data = player_data
        self.companies = companies
        self.on_back = on_back
        self.on_complete = on_complete

        self.show()

    def show(self):
        # Clear the window
        for widget in self.root.winfo_children():
            widget.destroy()

        # Title
        title_label = tk.Label(self.root, text="Character Creation", font=("Arial", 24), bg="black", fg="white")
        title_label.pack(pady=30)

        # Character creation form
        form_frame = tk.Frame(self.root, bg="black")
        form_frame.pack(pady=20)

        # Name input
        name_label = tk.Label(form_frame, text="Character Name:", font=("Arial", 14), bg="black", fg="white")
        name_label.grid(row=0, column=0, sticky="w", pady=10)

        self.name_entry = tk.Entry(form_frame, font=("Arial", 14), width=25)
        self.name_entry.grid(row=0, column=1, pady=10)

        # Random Name button
        def set_random_name():
            self.name_entry.delete(0, tk.END)
            self.name_entry.insert(0, random.choice(NPC_NAMES))

        random_name_btn = tk.Button(form_frame, text="Random", font=("Arial", 12), command=set_random_name)
        random_name_btn.grid(row=0, column=2, padx=(5, 0), pady=10)

        # Department selection
        department_label = tk.Label(form_frame, text="Department:", font=("Arial", 14), bg="black", fg="white")
        department_label.grid(row=1, column=0, sticky="w", pady=10)

        self.department_var = tk.StringVar(value=SELECT_DEPARTMENT)
        department_names = [dept for dept, _ in group_jobs_by_department()]
        department_menu = tk.OptionMenu(
            form_frame,
            self.department_var,
            SELECT_DEPARTMENT,
            *department_names,
            command=self.on_department_selected,
        )
        department_menu.config(font=("Arial", 14), width=20)
        department_menu.grid(row=1, column=1, pady=10)

        # Job selection
        job_label = tk.Label(form_frame, text="Select Job:", font=("Arial", 14), bg="black", fg="white")
        job_label.grid(row=2, column=0, sticky="w", pady=10)

        self.job_var = tk.StringVar(value=SELECT_JOB)
        self.job_menu_frame = tk.Frame(form_frame, bg="black")
        self.job_menu_frame.grid(row=2, column=1, pady=10, sticky="w")

        # Credits display based on selected job
        credits_label = tk.Label(form_frame, text="Starting Credits:", font=("Arial", 14), bg="black", fg="white")
        credits_label.grid(row=3, column=0, sticky="w", pady=10)

        self.credits_value = tk.Label(form_frame, text="—", font=("Arial", 14), bg="black", fg="white")
        self.credits_value.grid(row=3, column=1, sticky="w", pady=10)

        # Job description frame
        desc_frame = tk.Frame(self.root, bg="black")
        desc_frame.pack(pady=10, fill=tk.X, padx=50)

        desc_label = tk.Label(desc_frame, text="Job Description:", font=("Arial", 14, "bold"), bg="black", fg="white")
        desc_label.pack(anchor=tk.W)

        self.job_description = tk.Label(desc_frame, text="", font=("Arial", 12), bg="black", fg="white", wraplength=700, justify=tk.LEFT)
        self.job_description.pack(anchor=tk.W, pady=5)

        self._rebuild_job_menu([SELECT_JOB])
        self.show_job_placeholder()

        # Buttons
        button_frame = tk.Frame(self.root, bg="black")
        button_frame.pack(pady=20)

        start_game_btn = tk.Button(button_frame, text="Start Game", font=("Arial", 14), width=15, command=self.start_game)
        start_game_btn.pack(side=tk.LEFT, padx=10)

        back_btn = tk.Button(button_frame, text="Back", font=("Arial", 14), width=15, command=self.on_back)
        back_btn.pack(side=tk.LEFT, padx=10)

    def _rebuild_job_menu(self, options, select_first=False):
        """Replace the job OptionMenu with a new set of options."""
        for widget in self.job_menu_frame.winfo_children():
            widget.destroy()

        if select_first and options:
            self.job_var.set(options[0])
        elif options:
            self.job_var.set(options[0])

        job_menu = tk.OptionMenu(
            self.job_menu_frame,
            self.job_var,
            *options,
            command=self.update_job_information,
        )
        job_menu.config(font=("Arial", 14), width=20)
        job_menu.pack()

        if select_first and options and options[0] in JOBS:
            self.update_job_information(options[0])
        else:
            self.show_job_placeholder()

    def on_department_selected(self, department):
        """Populate the job dropdown when a department is chosen."""
        if department == SELECT_DEPARTMENT:
            self._rebuild_job_menu([SELECT_JOB])
            return

        jobs = get_jobs_for_department(department)
        if jobs:
            self._rebuild_job_menu(jobs, select_first=True)
        else:
            self._rebuild_job_menu([SELECT_JOB])

    def show_job_placeholder(self):
        """Show placeholder text when no valid job is selected."""
        if not hasattr(self, "credits_value") or not hasattr(self, "job_description"):
            return
        self.credits_value.config(text="—")
        self.job_description.config(text="Select a department and job to see details.")

    def update_job_information(self, job_name):
        """Update the job description and credits display based on selected job"""
        if not hasattr(self, "credits_value") or not hasattr(self, "job_description"):
            return
        if job_name not in JOBS:
            self.show_job_placeholder()
            return

        job_info = JOBS[job_name]
        self.credits_value.config(text=f"{job_info['credits']} cr")
        self.job_description.config(text=job_info["description"])

    def start_game(self):
        # Get player information
        player_name = self.name_entry.get().strip()

        if not player_name:
            messagebox.showerror("Error", "Please enter a character name.")
            return

        if self.department_var.get() == SELECT_DEPARTMENT:
            messagebox.showerror("Error", "Please select a department.")
            return

        job = self.job_var.get()
        if job not in JOBS:
            messagebox.showerror("Error", "Please select a job.")
            return

        job_info = JOBS[job]

        self.player_data["name"] = player_name
        self.player_data["job"] = job
        self.player_data["department"] = job_info["department"]
        self.player_data["subdepartment"] = job_info["subdepartment"]
        self.player_data["inventory"] = []
        self.player_data["locker_inventory"] = build_default_locker_inventory()
        self.player_data["location"] = {"x": -1, "y": 0}
        self.player_data["stock_holdings"] = {}

        # Initialize damage stats
        self.player_data["damage"] = {
            "burn": 0,
            "poison": 0,
            "oxygen": 0
        }

        self.player_data["credits"] = job_info["credits"]

        # Set job-specific permissions for room access
        if job == "Captain":
            # Captain has access to all stations
            self.player_data["permissions"] = {
                "security_station": True,
                "medbay_station": True,
                "bridge_station": True,
                "engineering_station": True,
                "bar_station": True,
                "hop_station": True,
                "botany_station": True
            }
        elif job == "Head of Personnel":
            # HoP has access to HoP station, Bar station, and Botany station
            self.player_data["permissions"] = {
                "security_station": False,
                "medbay_station": False,
                "bridge_station": False,
                "engineering_station": False,
                "bar_station": True,
                "hop_station": True,
                "botany_station": True
            }
        elif job == "Botanist":
            # Botanist has access to Botany station
            self.player_data["permissions"] = {
                "security_station": False,
                "medbay_station": False,
                "bridge_station": False,
                "engineering_station": False,
                "bar_station": False,
                "hop_station": False,
                "botany_station": True
            }
        else:
            # Other jobs have specific access
            self.player_data["permissions"] = {
                "security_station": job == "Security Guard",
                "medbay_station": job == "Doctor",
                "bridge_station": job == "Captain",
                "engineering_station": job == "Engineer",
                "bar_station": job == "Bartender",
                "hop_station": False,
                "botany_station": job == "Botanist"
            }

        # --- NPC Generation ---
        station_crew = []  # Fresh crew list for new game
        available_names = NPC_NAMES.copy()
        if player_name in available_names:
             available_names.remove(player_name) # Avoid duplicate names

        department_heads = {
            "Captain": {"credits": 10000, "station": "bridge_station"},
            "Head of Personnel": {"credits": 9000, "station": "hop_station"},
            "Security Guard": {"credits": 5000, "station": "security_station"},
            "Doctor": {"credits": 7500, "station": "medbay_station"},
            "Engineer": {"credits": 2500, "station": "engineering_station"},
            "Botanist": {"credits": 3000, "station": "botany_station"},
            "Bartender": {"credits": 3500, "station": "bar_station"}
        }

        for npc_job, data in department_heads.items():
            if npc_job != job: # If the player didn't take this job
                if not available_names:
                    npc_name = f"NPC_{npc_job.replace(' ', '')}" # Fallback name
                else:
                    npc_name = random.choice(available_names)
                    available_names.remove(npc_name)

                npc_data = {
                    "name": npc_name,
                    "job": npc_job,
                    "credits": data["credits"], # Give them starting credits too
                    "inventory": [], # Empty inventory for now
                    "location": {"x": -1, "y": 0}, # Start in quarters for simplicity
                    "limbs": { # Same starting health as player
                        "left_arm": 100, "right_arm": 100, "left_leg": 100,
                        "right_leg": 100, "chest": 100, "head": 100
                    },
                    "damage": {"burn": 0, "poison": 0, "oxygen": 0},
                     "permissions": {s: (j == npc_job) for j, d in department_heads.items() for s in [d["station"]]} # Basic permission for their station
                }
                # Add special permissions for NPC Captain/HoP if generated
                if npc_job == "Captain":
                    npc_data["permissions"] = {d["station"]: True for d in department_heads.values()}
                elif npc_job == "Head of Personnel":
                    npc_data["permissions"]["bar_station"] = True
                    npc_data["permissions"]["botany_station"] = True

                station_crew.append(npc_data)
                print(f"Generated NPC: {npc_name} ({npc_job})") # Debug print
        # --- End NPC Generation ---

        # Initialize stock market with starting values
        if "stock_market" not in self.player_data:
            self.player_data["stock_market"] = default_stock_market_state()
            self.player_data["stock_market"]["companies"] = serialize_companies(self.companies)

        # Initialize station power - Solar panels default ON unless player can control them
        can_control_power = job in ["Engineer", "Captain"]
        self.player_data["station_power"] = {
            "battery_level": 25.0,
            "solar_charging": not can_control_power,  # True if player can't control, False otherwise
            "last_update_time": datetime.datetime.now().isoformat(),
            "system_levels": {
                "life_support": 10,
                "hallway_lighting": 5,
                "security_systems": 7,
                "communication_array": 5
            },
            "power_mode": "balanced"
        }

        self.player_data["station_crew"] = station_crew

        # Hand the finished character and crew back to the game
        self.on_complete(self.player_data, station_crew)
