"""
WinPulse Monitor - Lightweight System Resource & Process Manager.
Designed for Windows 10/11 single-user process monitoring and RAM optimization.
"""

import getpass
import tkinter as tk
from tkinter import messagebox, ttk
import psutil


class WinPulseApp:
    """Main application class for the WinPulse System Monitor GUI."""

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("WinPulse Monitor - System & Process Manager")
        self.root.geometry("720x480")
        self.root.configure(bg="#181825")
        self.root.resizable(False, False)

        # Get current Windows username to filter single-user processes
        self.current_user = getpass.getuser()

        self._setup_styles()
        self._build_ui()
        self.update_stats()
        self.refresh_processes()

    def _setup_styles(self) -> None:
        """Configure dark theme styles for Tkinter Treeview and widgets."""
        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "Treeview",
            background="#1e1e2e",
            foreground="#cdd6f4",
            fieldbackground="#1e1e2e",
            rowheight=26,
            font=("Consolas", 10),
        )
        style.configure(
            "Treeview.Heading",
            background="#313244",
            foreground="#89b4fa",
            font=("Segoe UI", 10, "bold"),
        )
        style.map("Treeview", background=[("selected", "#45475a")])

    def _build_ui(self) -> None:
        """Build the main graphical user interface."""
        # Top Header Frame
        header = tk.Frame(self.root, bg="#181825", pady=10)
        header.pack(fill=tk.X, padx=15)

        title_lbl = tk.Label(
            header,
            text=f"⚡ WinPulse Monitor | User: {self.current_user}",
            bg="#181825",
            fg="#89b4fa",
            font=("Segoe UI", 14, "bold"),
        )
        title_lbl.pack(side=tk.LEFT)

        # Live Metrics Frame (CPU & RAM)
        metrics_frame = tk.Frame(self.root, bg="#1e1e2e", pady=10, padx=15)
        metrics_frame.pack(fill=tk.X, padx=15, pady=(0, 10))

        self.cpu_label = tk.Label(
            metrics_frame,
            text="CPU Usage: 0.0%",
            bg="#1e1e2e",
            fg="#a6e3a1",
            font=("Consolas", 12, "bold"),
        )
        self.cpu_label.pack(side=tk.LEFT, padx=(0, 40))

        self.ram_label = tk.Label(
            metrics_frame,
            text="RAM Usage: 0.0 / 0.0 GB (0%)",
            bg="#1e1e2e",
            fg="#f9e2af",
            font=("Consolas", 12, "bold"),
        )
        self.ram_label.pack(side=tk.LEFT)

        # Process Table (Treeview)
        table_frame = tk.Frame(self.root, bg="#181825")
        table_frame.pack(fill=tk.BOTH, expand=True, padx=15)

        columns = ("pid", "name", "memory")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=11)
        self.tree.heading("pid", text="PID")
        self.tree.heading("name", text="Process Name")
        self.tree.heading("memory", text="RAM Usage (MB)")

        self.tree.column("pid", width=100, anchor=tk.CENTER)
        self.tree.column("name", width=380, anchor=tk.W)
        self.tree.column("memory", width=180, anchor=tk.E)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Bottom Control Buttons
        btn_frame = tk.Frame(self.root, bg="#181825", pady=12)
        btn_frame.pack(fill=tk.X, padx=15)

        refresh_btn = tk.Button(
            btn_frame,
            text="🔄 Refresh Processes",
            command=self.refresh_processes,
            bg="#89b4fa",
            fg="#11111b",
            font=("Segoe UI", 10, "bold"),
            relief=tk.FLAT,
            padx=12,
            pady=5,
        )
        refresh_btn.pack(side=tk.LEFT)

        kill_btn = tk.Button(
            btn_frame,
            text="🛑 Terminate Selected Process",
            command=self.terminate_selected,
            bg="#f38ba8",
            fg="#11111b",
            font=("Segoe UI", 10, "bold"),
            relief=tk.FLAT,
            padx=12,
            pady=5,
        )
        kill_btn.pack(side=tk.RIGHT)

    def update_stats(self) -> None:
        """Update live CPU and RAM metrics every 2 seconds."""
        cpu_percent = psutil.cpu_percent(interval=None)
        mem = psutil.virtual_memory()
        used_gb = mem.used / (1024 ** 3)
        total_gb = mem.total / (1024 ** 3)

        self.cpu_label.config(text=f"CPU Usage: {cpu_percent:.1f}%")
        self.ram_label.config(
            text=f"RAM Usage: {used_gb:.1f} / {total_gb:.1f} GB ({mem.percent}%)"
        )
        self.root.after(2000, self.update_stats)

    def refresh_processes(self) -> None:
        """Fetch and sort active processes for the current Windows user by RAM usage."""
        for row in self.tree.get_children():
            self.tree.delete(row)

        process_list = []
        for proc in psutil.process_iter(["pid", "name", "username", "memory_info"]):
            try:
                info = proc.info
                username = info.get("username") or ""
                if self.current_user.lower() in username.lower():
                    mem_mb = info["memory_info"].rss / (1024 * 1024)
                    process_list.append((info["pid"], info["name"], mem_mb))
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue

        # Sort by RAM usage (highest first) and display top 50
        process_list.sort(key=lambda x: x[2], reverse=True)
        for pid, name, mem_mb in process_list[:50]:
            self.tree.insert("", tk.END, values=(pid, name, f"{mem_mb:.1f} MB"))

    def terminate_selected(self) -> None:
        """Safely terminate the selected user process."""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("No Selection", "Please select a process from the list first.")
            return

        item = self.tree.item(selected[0])
        pid, name, _ = item["values"]

        confirm = messagebox.askyesno(
            "Confirm Termination",
            f"Are you sure you want to terminate '{name}' (PID: {pid})?",
        )
        if confirm:
            try:
                proc = psutil.Process(int(pid))
                proc.terminate()
                self.root.after(500, self.refresh_processes)
                messagebox.showinfo("Success", f"Process '{name}' (PID: {pid}) has been terminated.")
            except (psutil.NoSuchProcess, psutil.AccessDenied) as err:
                messagebox.showerror("Error", f"Failed to terminate process:\n{err}")


if __name__ == "__main__":
    app_root = tk.Tk()
    app = WinPulseApp(app_root)
    app_root.mainloop()
