import tkinter as tk
from tkinter import ttk, messagebox
import socket
import threading
import time

class StagedLQRTunerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Staged LQR Robot Parameter Tuner")
        self.root.geometry("600x700")
        self.root.configure(bg='#2c3e50')
       
        # UDP settings
        self.esp32_ip = "192.168.1.100"  # Default IP - user can change this
        self.esp32_port = 5508
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
       
        # Variables for sliders - Stage 1 (Small angles 0-5°)
        self.k1_stage1_var = tk.DoubleVar(value=6.3)
        self.k2_stage1_var = tk.DoubleVar(value=0.43)
        
        # Stage 2 (Medium angles 5-15°)
        self.k1_stage2_var = tk.DoubleVar(value=13.0)
        self.k2_stage2_var = tk.DoubleVar(value=1.8)
        
        # Stage 3 (Large angles 15-30°)
        self.k1_stage3_var = tk.DoubleVar(value=17.0)
        self.k2_stage3_var = tk.DoubleVar(value=2.5)
        
        # Additional parameters
        self.smoothing_var = tk.DoubleVar(value=0.5)
        self.offset_var = tk.DoubleVar(value=0.0)
        
        self.auto_send = tk.BooleanVar(value=False)
       
        # Connection status
        self.connected = False
        self.last_send_time = 0
        
        # Track which stages have been sent
        self.stages_sent = [False, False, False]
       
        self.create_widgets()
        self.update_status()
       
    def create_widgets(self):
        # Title
        title = tk.Label(self.root, text="🤖 Staged LQR Robot Tuner",
                        font=("Arial", 18, "bold"),
                        bg='#2c3e50', fg='#ecf0f1')
        title.pack(pady=10)
       
        # Connection frame
        conn_frame = tk.Frame(self.root, bg='#2c3e50')
        conn_frame.pack(pady=5, padx=20, fill='x')
       
        tk.Label(conn_frame, text="ESP32 IP:",
                font=("Arial", 10), bg='#2c3e50', fg='#ecf0f1').pack(side='left')
       
        self.ip_entry = tk.Entry(conn_frame, font=("Arial", 10), width=15)
        self.ip_entry.insert(0, self.esp32_ip)
        self.ip_entry.pack(side='left', padx=(5,10))
       
        self.connect_btn = tk.Button(conn_frame, text="Test Connection",
                                   command=self.test_connection,
                                   bg='#3498db', fg='white',
                                   font=("Arial", 9, "bold"))
        self.connect_btn.pack(side='left')
       
        self.status_label = tk.Label(conn_frame, text="● Disconnected",
                                   font=("Arial", 9), bg='#2c3e50', fg='#e74c3c')
        self.status_label.pack(side='right')
       
        # Create notebook for tabbed interface
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(pady=10, padx=20, fill='both', expand=True)
        
        # Configure notebook style
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TNotebook', background='#34495e')
        style.configure('TNotebook.Tab', background='#2c3e50', foreground='#ecf0f1', padding=[10, 5])
        style.map('TNotebook.Tab', background=[('selected', '#3498db')])
       
        # Create tabs for each stage
        self.create_stage_tab("Stage 1: Small Angles (0-5°)", 
                             self.k1_stage1_var, self.k2_stage1_var, 1, '#27ae60')
        self.create_stage_tab("Stage 2: Medium Angles (5-15°)", 
                             self.k1_stage2_var, self.k2_stage2_var, 2, '#f39c12')
        self.create_stage_tab("Stage 3: Large Angles (15-30°)", 
                             self.k1_stage3_var, self.k2_stage3_var, 3, '#e74c3c')
        
        # Additional parameters tab
        self.create_additional_params_tab()
        
        # Control buttons frame (below notebook)
        btn_frame = tk.Frame(self.root, bg='#2c3e50')
        btn_frame.pack(pady=10)
       
        # Auto-send checkbox
        auto_check = tk.Checkbutton(btn_frame, text="Auto Send Changes",
                                  variable=self.auto_send,
                                  font=("Arial", 10),
                                  bg='#2c3e50', fg='#ecf0f1',
                                  selectcolor='#34495e',
                                  command=self.toggle_auto_send)
        auto_check.pack(side='left', padx=10)
       
        # Send all button
        self.send_all_btn = tk.Button(btn_frame, text="Send All Parameters",
                                     command=self.send_all_parameters,
                                     bg='#27ae60', fg='white',
                                     font=("Arial", 11, "bold"),
                                     width=18)
        self.send_all_btn.pack(side='left', padx=10)
        
        # Send current stage button
        self.send_stage_btn = tk.Button(btn_frame, text="Send Current Stage",
                                       command=self.send_current_stage,
                                       bg='#3498db', fg='white',
                                       font=("Arial", 11, "bold"),
                                       width=18)
        self.send_stage_btn.pack(side='left', padx=5)
       
        # Reset button
        reset_btn = tk.Button(btn_frame, text="Reset All",
                            command=self.reset_defaults,
                            bg='#e67e22', fg='white',
                            font=("Arial", 11, "bold"),
                            width=12)
        reset_btn.pack(side='left', padx=5)
       
        # Status text area
        status_frame = tk.Frame(self.root, bg='#2c3e50')
        status_frame.pack(pady=10, padx=20, fill='x')
       
        tk.Label(status_frame, text="Status Log:",
                font=("Arial", 10, "bold"), bg='#2c3e50', fg='#ecf0f1').pack(anchor='w')
       
        self.status_text = tk.Text(status_frame, height=5, width=70,
                                 font=("Courier", 9),
                                 bg='#1a1a1a', fg='#00ff00')
        self.status_text.pack(fill='x')
        self.status_text.insert('end', "Ready to connect... Robot needs ALL stage gains before balancing starts!\n")

    def create_stage_tab(self, title, k1_var, k2_var, stage_num, color):
        # Create frame for this stage
        stage_frame = tk.Frame(self.notebook, bg='#34495e')
        self.notebook.add(stage_frame, text=f"Stage {stage_num}")
        
        # Stage info
        info_frame = tk.Frame(stage_frame, bg='#34495e')
        info_frame.pack(pady=10, padx=20, fill='x')
        
        tk.Label(info_frame, text=title,
                font=("Arial", 14, "bold"),
                bg='#34495e', fg=color).pack()
        
        # Stage description
        descriptions = {
            1: "Smooth control for small deviations\nRecommended: K1=4-8, K2=0.2-0.6",
            2: "Moderate control for medium angles\nRecommended: K1=10-16, K2=1.0-2.5", 
            3: "Aggressive control for large angles\nRecommended: K1=15-20, K2=2.0-3.5"
        }
        
        tk.Label(info_frame, text=descriptions[stage_num],
                font=("Arial", 10),
                bg='#34495e', fg='#bdc3c7',
                justify='center').pack(pady=5)
        
        # K1 Slider
        self.create_slider_section(stage_frame, "K1 (Angle Gain)",
                                 k1_var, 0.1, 30.0, 0.1, color)
       
        # K2 Slider  
        self.create_slider_section(stage_frame, "K2 (Angular Velocity Gain)",
                                 k2_var, 0.01, 5.0, 0.01, color)
        
        # Send this stage button
        send_frame = tk.Frame(stage_frame, bg='#34495e')
        send_frame.pack(pady=20)
        
        send_btn = tk.Button(send_frame, text=f"Send Stage {stage_num}",
                           command=lambda: self.send_stage_parameters(stage_num),
                           bg=color, fg='white',
                           font=("Arial", 12, "bold"),
                           width=15)
        send_btn.pack()
        
        # Status indicator for this stage
        status_label = tk.Label(send_frame, text="Not Sent",
                              font=("Arial", 10),
                              bg='#34495e', fg='#e74c3c')
        status_label.pack(pady=5)
        
        # Store reference to status label
        setattr(self, f'stage{stage_num}_status', status_label)

    def create_additional_params_tab(self):
        # Additional parameters tab
        params_frame = tk.Frame(self.notebook, bg='#34495e')
        self.notebook.add(params_frame, text="Advanced")
        
        tk.Label(params_frame, text="Advanced Parameters",
                font=("Arial", 14, "bold"),
                bg='#34495e', fg='#9b59b6').pack(pady=10)
        
        # Smoothing slider
        self.create_slider_section(params_frame, "Transition Smoothing (0.0-1.0)",
                                 self.smoothing_var, 0.0, 1.0, 0.05, '#9b59b6')
        
        tk.Label(params_frame, text="Higher values = smoother transitions between stages",
                font=("Arial", 9), bg='#34495e', fg='#bdc3c7').pack()
        
        # Offset slider
        self.create_slider_section(params_frame, "Pitch Offset (-10.0 to +10.0)",
                                 self.offset_var, -10.0, 10.0, 0.1, '#9b59b6')
        
        tk.Label(params_frame, text="Adjust robot's balance point (+ leans forward, - leans backward)",
                font=("Arial", 9), bg='#34495e', fg='#bdc3c7').pack()
        
        # Send advanced params button
        send_frame = tk.Frame(params_frame, bg='#34495e')
        send_frame.pack(pady=20)
        
        send_btn = tk.Button(send_frame, text="Send Advanced Params",
                           command=self.send_advanced_parameters,
                           bg='#9b59b6', fg='white',
                           font=("Arial", 12, "bold"),
                           width=20)
        send_btn.pack()
   
    def create_slider_section(self, parent, title, var, min_val, max_val, resolution, color):
        frame = tk.Frame(parent, bg='#34495e')
        frame.pack(pady=15, padx=20, fill='x')
       
        # Title and value display
        title_frame = tk.Frame(frame, bg='#34495e')
        title_frame.pack(fill='x')
       
        tk.Label(title_frame, text=title,
                font=("Arial", 12, "bold"),
                bg='#34495e', fg='#ecf0f1').pack(side='left')
       
        value_label = tk.Label(title_frame, text=f"{var.get():.3f}",
                             font=("Arial", 12, "bold"),
                             bg='#34495e', fg=color)
        value_label.pack(side='right')
       
        # Slider
        slider = tk.Scale(frame, from_=min_val, to=max_val,
                         resolution=resolution,
                         variable=var, orient='horizontal',
                         font=("Arial", 10),
                         bg='#34495e', fg='#ecf0f1',
                         troughcolor='#2c3e50',
                         activebackground=color,
                         highlightthickness=0,
                         command=lambda val: self.on_slider_change(val, value_label, var))
        slider.pack(fill='x', pady=5)
       
        return slider
   
    def on_slider_change(self, val, value_label, var):
        value_label.config(text=f"{var.get():.3f}")
        if self.auto_send.get():
            # Debounce auto-send to avoid spam
            current_time = time.time()
            if current_time - self.last_send_time > 0.2:  # 200ms debounce
                self.send_current_stage()
                self.last_send_time = current_time
   
    def test_connection(self):
        self.esp32_ip = self.ip_entry.get()
        try:
            # Send STATUS command to test connection
            test_msg = "STATUS"
            self.sock.sendto(test_msg.encode(), (self.esp32_ip, self.esp32_port))
            self.connected = True
            self.status_label.config(text="● Connected", fg='#27ae60')
            self.log_status(f"✓ Connected to {self.esp32_ip}:{self.esp32_port}")
            self.log_status("✓ Ready to send parameters")
        except Exception as e:
            self.connected = False
            self.status_label.config(text="● Connection Failed", fg='#e74c3c')
            self.log_status(f"✗ Connection failed: {str(e)}")
            messagebox.showerror("Connection Error", f"Failed to connect to {self.esp32_ip}:{self.esp32_port}\n\n{str(e)}")
   
    def send_stage_parameters(self, stage_num):
        if not self.connected:
            messagebox.showwarning("Not Connected", "Please test connection first!")
            return
            
        try:
            if stage_num == 1:
                k1_val = self.k1_stage1_var.get()
                k2_val = self.k2_stage1_var.get()
            elif stage_num == 2:
                k1_val = self.k1_stage2_var.get()
                k2_val = self.k2_stage2_var.get()
            else:  # stage 3
                k1_val = self.k1_stage3_var.get()
                k2_val = self.k2_stage3_var.get()
            
            message = f"S{stage_num}:{k1_val:.3f},{k2_val:.3f}"
            self.sock.sendto(message.encode(), (self.esp32_ip, self.esp32_port))
            
            # Update status
            self.stages_sent[stage_num-1] = True
            status_label = getattr(self, f'stage{stage_num}_status')
            status_label.config(text="✓ Sent", fg='#27ae60')
            
            self.log_status(f"→ Stage {stage_num}: K1={k1_val:.3f}, K2={k2_val:.3f}")
            
        except Exception as e:
            self.log_status(f"✗ Failed to send Stage {stage_num}: {str(e)}")
            self.connected = False
            self.status_label.config(text="● Disconnected", fg='#e74c3c')

    def send_current_stage(self):
        # Get currently selected tab
        current_tab = self.notebook.index(self.notebook.select())
        if current_tab < 3:  # Stage tabs (0, 1, 2)
            self.send_stage_parameters(current_tab + 1)
        else:  # Advanced tab
            self.send_advanced_parameters()

    def send_advanced_parameters(self):
        if not self.connected:
            messagebox.showwarning("Not Connected", "Please test connection first!")
            return
            
        try:
            # Send smoothing
            smooth_val = self.smoothing_var.get()
            smooth_msg = f"SMOOTH:{smooth_val:.3f}"
            self.sock.sendto(smooth_msg.encode(), (self.esp32_ip, self.esp32_port))
            
            time.sleep(0.1)  # Small delay between commands
            
            # Send offset
            offset_val = self.offset_var.get()
            offset_msg = f"OFFSET:{offset_val:.3f}"
            self.sock.sendto(offset_msg.encode(), (self.esp32_ip, self.esp32_port))
            
            self.log_status(f"→ Advanced: Smoothing={smooth_val:.3f}, Offset={offset_val:.3f}")
            
        except Exception as e:
            self.log_status(f"✗ Failed to send advanced parameters: {str(e)}")
            self.connected = False
            self.status_label.config(text="● Disconnected", fg='#e74c3c')

    def send_all_parameters(self):
        if not self.connected:
            messagebox.showwarning("Not Connected", "Please test connection first!")
            return
        
        # Send all stages
        for stage in range(1, 4):
            self.send_stage_parameters(stage)
            time.sleep(0.1)  # Small delay between commands
        
        # Send advanced parameters
        time.sleep(0.1)
        self.send_advanced_parameters()
        
        self.log_status("✓ All parameters sent! Robot should be ready to balance.")

    def reset_defaults(self):
        # Reset to default values
        self.k1_stage1_var.set(6.3)
        self.k2_stage1_var.set(0.43)
        self.k1_stage2_var.set(13.0)
        self.k2_stage2_var.set(1.8)
        self.k1_stage3_var.set(17.0)
        self.k2_stage3_var.set(2.5)
        self.smoothing_var.set(0.5)
        self.offset_var.set(0.0)
        
        # Reset status indicators
        for i in range(3):
            self.stages_sent[i] = False
            status_label = getattr(self, f'stage{i+1}_status')
            status_label.config(text="Not Sent", fg='#e74c3c')
        
        self.log_status("↻ Reset to defaults")
        
        if self.auto_send.get() and self.connected:
            self.send_all_parameters()
   
    def toggle_auto_send(self):
        if self.auto_send.get():
            self.log_status("🔄 Auto-send enabled")
        else:
            self.log_status("⏸ Auto-send disabled")
   
    def log_status(self, message):
        timestamp = time.strftime('%H:%M:%S')
        self.status_text.insert('end', f"{timestamp} - {message}\n")
        self.status_text.see('end')
        # Keep only last 100 lines
        lines = self.status_text.get('1.0', 'end').split('\n')
        if len(lines) > 100:
            self.status_text.delete('1.0', f'{len(lines)-100}.0')
   
    def update_status(self):
        # Periodic status update - could add connection heartbeat here
        self.root.after(2000, self.update_status)
   
    def on_closing(self):
        self.sock.close()
        self.root.destroy()

def main():
    root = tk.Tk()
    app = StagedLQRTunerGUI(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()

if __name__ == "__main__":
    main()