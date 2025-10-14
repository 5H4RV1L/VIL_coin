import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
from datetime import datetime
from VILcoin import Blockchain, Colors
from datetime import datetime
import sys
import queue
import os

if os.name == 'nt': 
    import ctypes
    ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)

class ConsoleRedirector:
    def __init__(self, console_callback):
        self.console_callback = console_callback
        self.queue = queue.Queue()
        
    def write(self, message):
        if message.strip(): 
            self.console_callback(message.strip())
        sys.__stdout__.write(message)
    
    def flush(self):
        sys.__stdout__.flush()

class VILCoinGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("VIL Coin Blockchain Network")
        self.root.geometry("1000x750")
        self.root.configure(bg='#0f0f23')
        
        self.console_buffer = []
        
        self.colors = {
            'bg_dark': '#0f0f23',
            'bg_medium': '#1a1a2e',
            'bg_light': '#252540',
            'accent': '#00d9ff',
            'accent_hover': '#00b8d4',
            'success': '#00ff88',
            'warning': '#ffaa00',
            'error': '#ff3366',
            'text': '#ffffff',
            'text_dim': '#a0a0b0'
        }
        
        sys.stdout = ConsoleRedirector(self.buffer_console_message)
        sys.stderr = ConsoleRedirector(self.buffer_console_message)
        
        self.blockchain = None
        self.init_blockchain()
        
        self.main_container = tk.Frame(root, bg=self.colors['bg_dark'])
        self.main_container.pack(fill=tk.BOTH, expand=True)
        
        self.root.after(100, self.setup_fullscreen)
        
        self.setup_styles()
        
        self.show_login_screen()
        
    def buffer_console_message(self, message):
        self.console_buffer.append(message)

        if len(self.console_buffer) > 100:
            self.console_buffer.pop(0)

        if hasattr(self, 'console_text'):
            try:
                self.display_console_message(message)
            except tk.TclError:
                pass

    def display_console_message(self, message):
        self.console_text.config(state=tk.NORMAL)
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.console_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.console_text.see(tk.END)
        self.console_text.config(state=tk.DISABLED)

    def add_console_message(self, message):
        print(message)  

    def setup_fullscreen(self):
        try:
            self.root.attributes('-fullscreen', True)
        except:
            try:
                self.root.state('zoomed')
            except:
                try:
                    self.root.attributes('-zoomed', True)
                except:
                    self.root.geometry(f"{self.root.winfo_screenwidth()}x{self.root.winfo_screenheight()}+0+0")
        
        self.root.bind('<Escape>', lambda e: self.toggle_fullscreen())
        self.root.bind('<F11>', lambda e: self.toggle_fullscreen())
    
    def toggle_fullscreen(self):
        try:
            current_state = self.root.attributes('-fullscreen')
            self.root.attributes('-fullscreen', not current_state)
        except:
            pass
    
    
    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        
        style.configure('TFrame', background=self.colors['bg_dark'])
        style.configure('Card.TFrame', background=self.colors['bg_medium'], relief='flat')
        
        style.configure('TLabel', 
            background=self.colors['bg_dark'], 
            foreground=self.colors['text'], 
            font=('Segoe UI', 10))
        style.configure('Title.TLabel', 
            font=('Segoe UI', 28, 'bold'), 
            foreground=self.colors['accent'])
        style.configure('Header.TLabel', 
            font=('Segoe UI', 20, 'bold'), 
            foreground=self.colors['accent'])
        style.configure('Subheader.TLabel',
            font=('Segoe UI', 11),
            foreground=self.colors['text_dim'])
        style.configure('Balance.TLabel',
            font=('Segoe UI', 32, 'bold'),
            foreground=self.colors['success'])
        
        style.configure('TEntry',
            fieldbackground=self.colors['bg_light'],
            foreground=self.colors['text'],
            borderwidth=0,
            relief='flat')
        
        style.configure('TButton', 
            font=('Segoe UI', 10, 'bold'),
            borderwidth=0,
            relief='flat',
            padding=(20, 10))
        style.map('TButton',
            background=[('active', self.colors['bg_light'])])
        
        style.configure('Primary.TButton',
            background=self.colors['accent'],
            foreground='#000000',
            font=('Segoe UI', 11, 'bold'))
        style.map('Primary.TButton',
            background=[('active', self.colors['accent_hover'])])
        
        style.configure('Success.TButton',
            background=self.colors['success'],
            foreground='#000000')
        style.map('Success.TButton',
            background=[('active', '#00dd77')])
            
        style.configure('Danger.TButton',
            background=self.colors['error'],
            foreground='#ffffff')
    
    def create_card(self, parent, **kwargs):
        card = tk.Frame(parent, bg=self.colors['bg_medium'], **kwargs)
        return card
    
    def create_gradient_label(self, parent, text, font_size=28):
        label = tk.Label(parent, 
            text=text,
            bg=self.colors['bg_dark'],
            fg=self.colors['accent'],
            font=('Segoe UI', font_size, 'bold'))
        return label
    
    def init_blockchain(self):
        def init():
            self.blockchain = Blockchain()
        
        thread = threading.Thread(target=init, daemon=True)
        thread.start()
    
    def clear_container(self):
        for widget in self.main_container.winfo_children():
            widget.destroy()
    
    def show_login_screen(self):
        self.clear_container()

        close_btn = tk.Button(self.main_container,
            text="✕",
            bg=self.colors['error'],
            fg='#ffffff',
            font=('Segoe UI', 16, 'bold'),
            border=0,
            cursor='hand2',
            command=self.root.quit,
            padx=15,
            pady=5)
        close_btn.place(relx=1.0, rely=0.0, anchor='ne', x=-20, y=20)
        
        center_frame = tk.Frame(self.main_container, bg=self.colors['bg_dark'])
        center_frame.place(relx=0.5, rely=0.5, anchor='center')
        
        title = self.create_gradient_label(center_frame, "🪙 VIL COIN", 36)
        title.pack(pady=(0, 5))
        
        subtitle = tk.Label(center_frame,
            text="Decentralized Digital Currency",
            bg=self.colors['bg_dark'],
            fg=self.colors['text_dim'],
            font=('Segoe UI', 11))
        subtitle.pack(pady=(0, 30))
        
        if self.blockchain:
            info_card = self.create_card(center_frame)
            info_card.pack(pady=(0, 30), padx=40)
            
            status_label = tk.Label(info_card,
                text="● ONLINE",
                bg=self.colors['bg_medium'],
                fg=self.colors['success'],
                font=('Segoe UI', 9, 'bold'))
            status_label.pack(pady=5, padx=20)
            
            info_text = f"{self.blockchain.my_ip}:{self.blockchain.server_port}"
            info_label = tk.Label(info_card,
                text=info_text,
                bg=self.colors['bg_medium'],
                fg=self.colors['text_dim'],
                font=('Courier', 9))
            info_label.pack(pady=(0, 5), padx=20)
        
        login_card = self.create_card(center_frame)
        login_card.pack(pady=10, padx=40, fill=tk.BOTH)
        
        header_frame = tk.Frame(login_card, bg=self.colors['bg_medium'])
        header_frame.pack(fill=tk.X, pady=(20, 10))
        
        tk.Label(header_frame,
            text="Welcome Back",
            bg=self.colors['bg_medium'],
            fg=self.colors['text'],
            font=('Segoe UI', 16, 'bold')).pack()
        
        form_frame = tk.Frame(login_card, bg=self.colors['bg_medium'])
        form_frame.pack(pady=20, padx=40)
        
        tk.Label(form_frame, text="Username",
            bg=self.colors['bg_medium'],
            fg=self.colors['text_dim'],
            font=('Segoe UI', 9)).grid(row=0, column=0, sticky='w', pady=(0, 5))
        
        username_frame = tk.Frame(form_frame, bg=self.colors['bg_light'], highlightbackground=self.colors['accent'], highlightthickness=1)
        username_frame.grid(row=1, column=0, sticky='ew', pady=(0, 20))
        
        self.login_username = tk.Entry(username_frame,
            bg=self.colors['bg_light'],
            fg=self.colors['text'],
            font=('Segoe UI', 11),
            border=0,
            insertbackground=self.colors['accent'])
        self.login_username.pack(pady=12, padx=15, fill=tk.X)
        
        tk.Label(form_frame,
            text="Password",
            bg=self.colors['bg_medium'],
            fg=self.colors['text_dim'],
            font=('Segoe UI', 9)).grid(row=2, column=0, sticky='w', pady=(0, 5))
        
        password_frame = tk.Frame(form_frame, bg=self.colors['bg_light'], highlightbackground=self.colors['accent'], highlightthickness=1)
        password_frame.grid(row=3, column=0, sticky='ew', pady=(0, 20))
        
        self.login_password = tk.Entry(password_frame,
            bg=self.colors['bg_light'],
            fg=self.colors['text'],
            font=('Segoe UI', 11),
            border=0,
            show='●',
            insertbackground=self.colors['accent'])
        self.login_password.pack(pady=12, padx=15, fill=tk.X)
        
        form_frame.columnconfigure(0, minsize=300)
        
        btn_frame = tk.Frame(login_card, bg=self.colors['bg_medium'])
        btn_frame.pack(pady=(0, 25), padx=40, fill=tk.X)
        
        login_btn = tk.Button(btn_frame,
            text="LOGIN",
            bg=self.colors['accent'],
            fg='#000000',
            font=('Segoe UI', 11, 'bold'),
            border=0,
            cursor='hand2',
            command=self.login)
        login_btn.pack(fill=tk.X, pady=(0, 10))
        login_btn.config(height=2)
        
        create_btn = tk.Button(btn_frame,
            text="Create New Account",
            bg=self.colors['bg_light'],
            fg=self.colors['text'],
            font=('Segoe UI', 10),
            border=0,
            cursor='hand2',
            command=self.show_create_account)
        create_btn.pack(fill=tk.X, pady=(0, 10))
        create_btn.config(height=2)
        
        network_btn = tk.Button(btn_frame,
            text="🌐 Network Info",
            bg=self.colors['bg_dark'],
            fg=self.colors['text_dim'],
            font=('Segoe UI', 9),
            border=0,
            cursor='hand2',
            command=self.show_network_info_dialog)
        network_btn.pack()
    
    def show_create_account(self):
        self.clear_container()
        
        center_frame = tk.Frame(self.main_container, bg=self.colors['bg_dark'])
        center_frame.place(relx=0.5, rely=0.5, anchor='center')
        
        title = self.create_gradient_label(center_frame, "Create Account", 28)
        title.pack(pady=(0, 5))
        
        subtitle = tk.Label(center_frame,
            text="Join the VIL Coin Network",
            bg=self.colors['bg_dark'],
            fg=self.colors['text_dim'],
            font=('Segoe UI', 11))
        subtitle.pack(pady=(0, 30))
        
        form_card = self.create_card(center_frame)
        form_card.pack(pady=10, padx=40)
        
        form_frame = tk.Frame(form_card, bg=self.colors['bg_medium'])
        form_frame.pack(pady=30, padx=40)
        
        tk.Label(form_frame,
            text="Choose Username",
            bg=self.colors['bg_medium'],
            fg=self.colors['text_dim'],
            font=('Segoe UI', 9)).grid(row=0, column=0, sticky='w', pady=(0, 5))
        
        username_frame = tk.Frame(form_frame, bg=self.colors['bg_light'], highlightbackground=self.colors['accent'], highlightthickness=1)
        username_frame.grid(row=1, column=0, sticky='ew', pady=(0, 20))
        
        self.new_username = tk.Entry(username_frame,
            bg=self.colors['bg_light'],
            fg=self.colors['text'],
            font=('Segoe UI', 11),
            border=0,
            insertbackground=self.colors['accent'])
        self.new_username.pack(pady=12, padx=15, fill=tk.X)
        
        tk.Label(form_frame,
            text="Create Password",
            bg=self.colors['bg_medium'],
            fg=self.colors['text_dim'],
            font=('Segoe UI', 9)).grid(row=2, column=0, sticky='w', pady=(0, 5))
        
        password_frame = tk.Frame(form_frame, bg=self.colors['bg_light'], highlightbackground=self.colors['accent'], highlightthickness=1)
        password_frame.grid(row=3, column=0, sticky='ew', pady=(0, 20))
        
        self.new_password = tk.Entry(password_frame,
            bg=self.colors['bg_light'],
            fg=self.colors['text'],
            font=('Segoe UI', 11),
            border=0,
            show='●',
            insertbackground=self.colors['accent'])
        self.new_password.pack(pady=12, padx=15, fill=tk.X)
        
        tk.Label(form_frame,
            text="Confirm Password",
            bg=self.colors['bg_medium'],
            fg=self.colors['text_dim'],
            font=('Segoe UI', 9)).grid(row=4, column=0, sticky='w', pady=(0, 5))
        
        confirm_frame = tk.Frame(form_frame, bg=self.colors['bg_light'], highlightbackground=self.colors['accent'], highlightthickness=1)
        confirm_frame.grid(row=5, column=0, sticky='ew', pady=(0, 20))
        
        self.confirm_password = tk.Entry(confirm_frame,
            bg=self.colors['bg_light'],
            fg=self.colors['text'],
            font=('Segoe UI', 11),
            border=0,
            show='●',
            insertbackground=self.colors['accent'])
        self.confirm_password.pack(pady=12, padx=15, fill=tk.X)
        
        form_frame.columnconfigure(0, minsize=320)
        
        info_box = tk.Frame(form_card, bg=self.colors['bg_light'])
        info_box.pack(pady=(0, 20), padx=40, fill=tk.X)
        
        tk.Label(info_box,
            text="💰 You'll receive 1000 VIL coins as a welcome bonus!",
            bg=self.colors['bg_light'],
            fg=self.colors['success'],
            font=('Segoe UI', 9),
            wraplength=300).pack(pady=10, padx=15)
        
        btn_frame = tk.Frame(form_card, bg=self.colors['bg_medium'])
        btn_frame.pack(pady=(0, 30), padx=40, fill=tk.X)
        
        create_btn = tk.Button(btn_frame,
            text="CREATE ACCOUNT",
            bg=self.colors['success'],
            fg='#000000',
            font=('Segoe UI', 11, 'bold'),
            border=0,
            cursor='hand2',
            command=self.create_account)
        create_btn.pack(fill=tk.X, pady=(0, 10))
        create_btn.config(height=2)
        
        back_btn = tk.Button(btn_frame,
            text="← Back to Login",
            bg=self.colors['bg_light'],
            fg=self.colors['text'],
            font=('Segoe UI', 10),
            border=0,
            cursor='hand2',
            command=self.show_login_screen)
        back_btn.pack(fill=tk.X)
        back_btn.config(height=2)
    
    def create_account(self):
        if not self.blockchain:
            messagebox.showerror("Error", "Blockchain not initialized yet!")
            return
        
        username = self.new_username.get().strip()
        password = self.new_password.get()
        confirm = self.confirm_password.get()
        
        if not username or not password:
            messagebox.showerror("Error", "Username and password cannot be empty!")
            return
        
        if password != confirm:
            messagebox.showerror("Error", "Passwords do not match!")
            return
        
        if self.blockchain.create_user(username, password):
            user_id = self.blockchain.users[username].user_id
            messagebox.showinfo("Success", f"🎉 Account created successfully!\n\nUser ID: {user_id}\nInitial balance: 1000 VIL coins")
            self.show_login_screen()
        else:
            messagebox.showerror("Error", "Username already exists!")
    
    def login(self):
        if not self.blockchain:
            messagebox.showerror("Error", "Blockchain not initialized yet!")
            return
        
        username = self.login_username.get().strip()
        password = self.login_password.get()
        
        if self.blockchain.login(username, password):
            self.show_main_dashboard()
        else:
            messagebox.showerror("Error", "Invalid username or password!")
    
    def show_main_dashboard(self):
        self.clear_container()
        
        dashboard = tk.Frame(self.main_container, bg='#0f0f1e')
        dashboard.pack(fill=tk.BOTH, expand=True, padx=40, pady=30)
        
        top_bar = tk.Frame(dashboard, bg='#0f0f1e')
        top_bar.pack(fill=tk.X, pady=(0, 30))
        
        user_id = self.blockchain.users[self.blockchain.current_user].user_id
        welcome_text = f"👤 {self.blockchain.current_user}"
        user_label = ttk.Label(top_bar, text=welcome_text, style='Header.TLabel')
        user_label.pack(side=tk.LEFT)
        
        id_label = ttk.Label(top_bar, text=f"ID: {user_id}", style='Info.TLabel')
        id_label.pack(side=tk.LEFT, padx=(20, 0))
        
        ttk.Button(top_bar, text="Logout", command=self.logout).pack(side=tk.RIGHT)
        
        balance_card = self.create_card(dashboard)
        balance_card.pack(fill=tk.X, pady=(0, 30))

        left_half = self.create_card(balance_card)
        left_half.pack(side=tk.LEFT, fill=tk.X, pady=(0, 30))

        balance_content = tk.Frame(left_half, bg='#1a1a2e')
        balance_content.pack(padx=(200), pady=35)

        ttk.Label(balance_content, text="Your Balance", style='CardInfo.TLabel').pack()

        balance_display = tk.Frame(balance_content, bg='#1a1a2e')
        balance_display.pack(pady=(10, 0))

        refresh_btn = tk.Button(balance_display,
            text="🔄",
            bg=self.colors['bg_light'],
            fg=self.colors['accent'],
            font=('Segoe UI', 20),
            border=0,
            cursor='hand2',
            command=self.show_main_dashboard,
            padx=8,
            pady=5)
        refresh_btn.pack(side=tk.LEFT, padx=(0, 15))

        balance = self.blockchain.get_balance(self.blockchain.current_user)
        balance_text = f"{balance:.2f} VIL"
        ttk.Label(balance_display, text=balance_text, style='Balance.TLabel').pack(side=tk.LEFT)
        
        right_half = tk.Frame(balance_card, bg='#1a1a2e')
        right_half.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        console_header = tk.Frame(right_half, bg='#1a1a2e')
        console_header.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(console_header,
            text="📟 System Console",
            bg='#1a1a2e',
            fg=self.colors['text_dim'],
            font=('Segoe UI', 10, 'bold')).pack(side=tk.LEFT)
        
        self.console_text = scrolledtext.ScrolledText(right_half,
            wrap=tk.WORD,
            width=50,
            height=8,
            font=('Consolas', 8),
            bg=self.colors['bg_dark'],
            fg=self.colors['success'],
            insertbackground=self.colors['accent'],
            selectbackground=self.colors['accent'],
            selectforeground='#000000',
            border=0,
            state=tk.DISABLED)
        self.console_text.pack(fill=tk.BOTH, expand=True)
        
        self.add_console_message("System initialized")
        self.add_console_message(f"Node: {self.blockchain.my_ip}:{self.blockchain.server_port}")
        self.add_console_message(f"Blockchain height: {len(self.blockchain.chain)}")
        self.add_console_message(f"Peers: {len(self.blockchain.peers)}")
        self.add_console_message(f"Balance: {balance:.2f} VIL")
        
        self.console_text.pack(fill=tk.BOTH, expand=True)

        for msg in self.console_buffer[-20:]:  
            self.display_console_message(msg)
        
        actions_frame = tk.Frame(dashboard, bg='#0f0f1e')
        actions_frame.pack(fill=tk.BOTH, expand=True)
        
        for i in range(4):
            actions_frame.columnconfigure(i, weight=1, uniform="action")
        for i in range(2):
            actions_frame.rowconfigure(i, weight=1, uniform="action")
        
        actions = [
            ("💸 Send Coins", self.show_send_coins, "#00d9ff"),
            ("⛏️ Mine Block", self.mine_block, "#ff6b6b"),
            ("📊 Blockchain", self.show_blockchain, "#4ecdc4"),
            ("⏳ Pending", self.show_pending, "#ffd93d"),
            ("👥 All Users", self.show_users, "#a29bfe"),
            ("🌐 Network", self.show_network_info_dialog, "#fd79a8"),
            ("🔄 Sync", self.sync_network, "#74b9ff"),
            ("➕ Add Peer", self.add_peer_dialog, "#55efc4"),
        ]
        
        for idx, (text, command, color) in enumerate(actions):
            row = idx // 4
            col = idx % 4
            
            btn_container = tk.Frame(actions_frame, bg='#0f0f1e')
            btn_container.grid(row=row, column=col, padx=12, pady=12, sticky='nsew')
            
            btn_card = tk.Frame(btn_container, bg='#1a1a2e', relief='flat')
            btn_card.pack(fill=tk.BOTH, expand=True)
            
            btn = tk.Button(btn_card, 
                text=text, 
                command=command,
                font=('Segoe UI', 20, 'bold'),
                bg='#1a1a2e',
                fg='#ffffff',
                activebackground='#252538',
                activeforeground='#ffffff',
                relief='flat',
                bd=0,
                cursor='hand2',
                padx=20,
                pady=30)
            btn.pack(fill=tk.BOTH, expand=True)
            
            # Hover effect
            btn.bind('<Enter>', lambda e, b=btn: b.configure(bg='#252538'))
            btn.bind('<Leave>', lambda e, b=btn: b.configure(bg='#1a1a2e'))
    
    def logout(self):
        self.blockchain.logout()
        messagebox.showinfo("Logged Out", "You have been logged out successfully!")
        self.show_login_screen()
    
    def show_send_coins(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Send VIL Coins")
        dialog.geometry("450x600")
        dialog.configure(bg=self.colors['bg_dark'])
        
        title_frame = tk.Frame(dialog, bg=self.colors['bg_dark'])
        title_frame.pack(pady=20)
        
        tk.Label(title_frame,
            text="💸",
            bg=self.colors['bg_dark'],
            fg=self.colors['accent'],
            font=('Segoe UI', 36)).pack()
        
        tk.Label(title_frame,
            text="Send VIL Coins",
            bg=self.colors['bg_dark'],
            fg=self.colors['text'],
            font=('Segoe UI', 16, 'bold')).pack()
        
        form_card = self.create_card(dialog)
        form_card.pack(pady=10, padx=30, fill=tk.BOTH, expand=True)
        
        form_frame = tk.Frame(form_card, bg=self.colors['bg_medium'])
        form_frame.pack(pady=20, padx=30, fill=tk.BOTH, expand=True)
        
        tk.Label(form_frame,
            text="Receiver Username",
            bg=self.colors['bg_medium'],
            fg=self.colors['text_dim'],
            font=('Segoe UI', 9)).pack(anchor='w', pady=(10, 5))
        
        receiver_frame = tk.Frame(form_frame, bg=self.colors['bg_light'], highlightbackground=self.colors['accent'], highlightthickness=1)
        receiver_frame.pack(fill=tk.X, pady=(0, 20))
        
        receiver_entry = tk.Entry(receiver_frame,
            bg=self.colors['bg_light'],
            fg=self.colors['text'],
            font=('Segoe UI', 11),
            border=0,
            insertbackground=self.colors['accent'])
        receiver_entry.pack(pady=12, padx=15, fill=tk.X)
        
        tk.Label(form_frame,
            text="Amount (VIL)",
            bg=self.colors['bg_medium'],
            fg=self.colors['text_dim'],
            font=('Segoe UI', 9)).pack(anchor='w', pady=(0, 5))
        
        amount_frame = tk.Frame(form_frame, bg=self.colors['bg_light'], highlightbackground=self.colors['accent'], highlightthickness=1)
        amount_frame.pack(fill=tk.X, pady=(0, 20))
        
        amount_entry = tk.Entry(amount_frame,
            bg=self.colors['bg_light'],
            fg=self.colors['text'],
            font=('Segoe UI', 11),
            border=0,
            insertbackground=self.colors['accent'])
        amount_entry.pack(pady=12, padx=15, fill=tk.X)
        
        current_balance = self.blockchain.get_balance(self.blockchain.current_user)
        tk.Label(form_frame,
            text=f"Available: {current_balance:.2f} VIL",
            bg=self.colors['bg_medium'],
            fg=self.colors['success'],
            font=('Segoe UI', 9, 'bold')).pack(pady=10)
        
        def send():
            receiver = receiver_entry.get().strip()
            try:
                amount = float(amount_entry.get())
                
                if receiver == self.blockchain.current_user:
                    messagebox.showerror("Error", "Cannot send coins to yourself!")
                    return
                
                if receiver not in self.blockchain.users:
                    messagebox.showerror("Error", "Receiver not found!")
                    return
                
                if amount <= 0:
                    messagebox.showerror("Error", "Amount must be positive!")
                    return
                
                current_balance = self.blockchain.get_balance(self.blockchain.current_user)
                if current_balance < amount:
                    messagebox.showerror("Error", f"Insufficient funds! Your balance: {current_balance:.2f} VIL")
                    return
                
                if self.blockchain.create_transaction(self.blockchain.current_user, receiver, amount):
                    messagebox.showinfo("Success", f"✅ Sent {amount:.2f} VIL to {receiver}\n\nTransaction is pending. Mine a block to confirm.")
                    dialog.destroy()
                    self.show_main_dashboard()
                else:
                    messagebox.showerror("Error", "Transaction failed!")
            except ValueError:
                messagebox.showerror("Error", "Invalid amount!")
        
        send_btn = tk.Button(form_frame,
            text="SEND COINS",
            bg=self.colors['accent'],
            fg='#000000',
            font=('Segoe UI', 11, 'bold'),
            border=0,
            cursor='hand2',
            command=send)
        send_btn.pack(fill=tk.X, pady=(10, 0))
        send_btn.config(height=2)
    
    def mine_block(self):
        if not self.blockchain.pending_transactions:
            messagebox.showwarning("No Transactions", "⚠️ No pending transactions to mine!")
            return
        
        result = messagebox.askyesno("Mine Block", 
            f"⛏️ Mining Details:\n\n"
            f"• Pending transactions: {len(self.blockchain.pending_transactions)}\n"
            f"• Mining difficulty: {self.blockchain.difficulty}\n"
            f"• Reward: {self.blockchain.mining_reward} VIL\n\n"
            "Start mining? This may take some time.")
        
        if result:
            progress_dialog = tk.Toplevel(self.root)
            progress_dialog.title("Mining...")
            progress_dialog.geometry("350x200")
            progress_dialog.configure(bg=self.colors['bg_dark'])
            
            card = self.create_card(progress_dialog)
            card.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
            
            tk.Label(card,
                text="⛏️",
                bg=self.colors['bg_medium'],
                fg=self.colors['warning'],
                font=('Segoe UI', 32)).pack(pady=(20, 10))
            
            tk.Label(card,
                text="Mining in progress...",
                bg=self.colors['bg_medium'],
                fg=self.colors['text'],
                font=('Segoe UI', 12, 'bold')).pack()
            
            tk.Label(card,
                text="Please wait, this may take a moment...",
                bg=self.colors['bg_medium'],
                fg=self.colors['text_dim'],
                font=('Segoe UI', 9)).pack(pady=(5, 20))
            
            progress_dialog.update()
            
            def mine():
                success = self.blockchain.mine_pending_transactions(self.blockchain.current_user)
                progress_dialog.destroy()
                if success:
                    messagebox.showinfo("Success", "✅ Block mined successfully!\n\nYour reward has been added to your balance.")
                    self.show_main_dashboard()
                else:
                    messagebox.showerror("Error", "Mining failed!")
            
            threading.Thread(target=mine, daemon=True).start()
    
    def show_blockchain(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Blockchain Explorer")
        dialog.geometry("800x600")
        dialog.configure(bg=self.colors['bg_dark'])
        
        header = tk.Frame(dialog, bg=self.colors['bg_medium'])
        header.pack(fill=tk.X, padx=20, pady=20)
        
        tk.Label(header,
            text="🔗 Blockchain Explorer",
            bg=self.colors['bg_medium'],
            fg=self.colors['accent'],
            font=('Segoe UI', 16, 'bold')).pack(side=tk.LEFT, padx=20, pady=15)
        
        info_frame = tk.Frame(header, bg=self.colors['bg_medium'])
        info_frame.pack(side=tk.RIGHT, padx=20, pady=10)
        
        chain_valid = self.blockchain.is_chain_valid()
        status_color = self.colors['success'] if chain_valid else self.colors['error']
        status_text = "✓ VALID" if chain_valid else "✗ INVALID"
        
        tk.Label(info_frame,
            text=status_text,
            bg=status_color,
            fg='#000000' if chain_valid else '#ffffff',
            font=('Segoe UI', 9, 'bold'),
            padx=10,
            pady=5).pack(side=tk.LEFT, padx=5)
        
        tk.Label(info_frame,
            text=f"{len(self.blockchain.chain)} Blocks",
            bg=self.colors['bg_light'],
            fg=self.colors['text'],
            font=('Segoe UI', 9, 'bold'),
            padx=10,
            pady=5).pack(side=tk.LEFT, padx=5)
        
        text_area = scrolledtext.ScrolledText(dialog,
            wrap=tk.WORD,
            width=90,
            height=25,
            font=('Consolas', 9),
            bg=self.colors['bg_light'],
            fg=self.colors['text'],
            insertbackground=self.colors['accent'],
            selectbackground=self.colors['accent'],
            selectforeground='#000000',
            border=0)
        text_area.pack(padx=20, pady=(0, 20), fill=tk.BOTH, expand=True)
        
        for block in self.blockchain.chain[-100:]:
            text_area.insert(tk.END, f"\n{'═' * 75}\n")
            text_area.insert(tk.END, f"  BLOCK #{block.index}\n")
            text_area.insert(tk.END, f"{'═' * 75}\n\n")
            text_area.insert(tk.END, f"  📅 Timestamp: {datetime.fromtimestamp(block.timestamp).strftime('%Y-%m-%d %H:%M:%S')}\n")
            text_area.insert(tk.END, f"  🔐 Hash:      {block.hash[:50]}...\n")
            text_area.insert(tk.END, f"  🔗 Previous:  {block.previous_hash[:50]}...\n")
            text_area.insert(tk.END, f"  🎲 Nonce:     {block.nonce}\n\n")
            
            if block.transactions:
                text_area.insert(tk.END, f"  💼 Transactions ({len(block.transactions)}):\n")
                text_area.insert(tk.END, f"  {'-' * 71}\n")
                for tx in block.transactions:
                    if tx.tx_type == "mining_reward":
                        text_area.insert(tk.END, f"  🏆 REWARD → {tx.receiver}: {tx.amount:.2f} VIL\n")
                    else:
                        text_area.insert(tk.END, f"  💸 {tx.sender} → {tx.receiver}: {tx.amount:.2f} VIL\n")
            text_area.insert(tk.END, "\n")
        
        text_area.config(state=tk.DISABLED)
    
    def show_pending(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Pending Transactions")
        dialog.geometry("700x500")
        dialog.configure(bg=self.colors['bg_dark'])
        
        header = tk.Frame(dialog, bg=self.colors['bg_medium'])
        header.pack(fill=tk.X, padx=20, pady=20)
        
        tk.Label(header,
            text="⏳ Pending Transactions",
            bg=self.colors['bg_medium'],
            fg=self.colors['warning'],
            font=('Segoe UI', 16, 'bold')).pack(side=tk.LEFT, padx=20, pady=15)
        
        count_label = tk.Label(header,
            text=f"{len(self.blockchain.pending_transactions)} Pending",
            bg=self.colors['warning'],
            fg='#000000',
            font=('Segoe UI', 9, 'bold'),
            padx=10,
            pady=5)
        count_label.pack(side=tk.RIGHT, padx=20)
        
        text_area = scrolledtext.ScrolledText(dialog,
            wrap=tk.WORD,
            width=80,
            height=22,
            font=('Consolas', 12),
            bg=self.colors['bg_light'],
            fg=self.colors['text'],
            insertbackground=self.colors['accent'],
            selectbackground=self.colors['accent'],
            selectforeground='#000000',
            border=0)
        text_area.pack(padx=20, pady=(0, 20), fill=tk.BOTH, expand=True)
        
        if not self.blockchain.pending_transactions:
            text_area.insert(tk.END, "\n\n")
            text_area.insert(tk.END, "  " + "─" * 60 + "\n")
            text_area.insert(tk.END, "  │" + " " * 58 + "│\n")
            text_area.insert(tk.END, "  │" + " " * 18 + "No pending transactions" + " " * 17 + "│\n")
            text_area.insert(tk.END, "  │" + " " * 58 + "│\n")
            text_area.insert(tk.END, "  " + "─" * 60 + "\n")
        else:
            for i, tx in enumerate(self.blockchain.pending_transactions, 1):
                timestamp_str = datetime.fromtimestamp(tx.timestamp).strftime('%Y-%m-%d %H:%M:%S')
                
                text_area.insert(tk.END, f"\n  [{i}] {timestamp_str}\n")
                text_area.insert(tk.END, f"  {tx.sender} ──→ {tx.receiver}\n")
                text_area.insert(tk.END, f"  💰 Amount: {tx.amount:.2f} VIL\n")
                text_area.insert(tk.END, f"  {'─' * 65}\n")
        
        text_area.config(state=tk.DISABLED)
    
    def show_users(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("All Users")
        dialog.geometry("500x500")
        dialog.configure(bg=self.colors['bg_dark'])
        
        # Header
        header = tk.Frame(dialog, bg=self.colors['bg_medium'])
        header.pack(fill=tk.X, padx=20, pady=20)
        
        tk.Label(header,
            text="👥 All Users",
            bg=self.colors['bg_medium'],
            fg=self.colors['accent'],
            font=('Segoe UI', 16, 'bold')).pack(side=tk.LEFT, padx=20, pady=15)
        
        count_label = tk.Label(header,
            text=f"{len(self.blockchain.users)} Users",
            bg=self.colors['accent'],
            fg='#000000',
            font=('Segoe UI', 9, 'bold'),
            padx=10,
            pady=5)
        count_label.pack(side=tk.RIGHT, padx=20)
        
        list_frame = tk.Frame(dialog, bg=self.colors['bg_dark'])
        list_frame.pack(padx=20, pady=(0, 20), fill=tk.BOTH, expand=True)
        
        canvas = tk.Canvas(list_frame, bg=self.colors['bg_dark'], highlightthickness=0)
        scrollbar = tk.Scrollbar(list_frame, orient="vertical", command=canvas.yview)
        scrollable = tk.Frame(canvas, bg=self.colors['bg_dark'])
        
        scrollable.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        for username, user in self.blockchain.users.items():
            user_card = self.create_card(scrollable)
            user_card.pack(fill=tk.X, pady=5, expand=True)
            
            card_content = tk.Frame(user_card, bg=self.colors['bg_medium'])
            card_content.pack(fill=tk.BOTH, padx=15, pady=12, expand=True)
            
            left = tk.Frame(card_content, bg=self.colors['bg_medium'])
            left.pack(side=tk.LEFT, fill=tk.X, expand=True)
            
            is_online = username == self.blockchain.current_user
            status_color = self.colors['success'] if is_online else self.colors['text_dim']
            status_text = "● ONLINE" if is_online else "○ OFFLINE"
            
            tk.Label(left,
                text=username,
                bg=self.colors['bg_medium'],
                fg=self.colors['text'],
                font=('Segoe UI', 11, 'bold')).pack(anchor='w')
            
            tk.Label(left,
                text=status_text,
                bg=self.colors['bg_medium'],
                fg=status_color,
                font=('Segoe UI', 8)).pack(anchor='e')
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def show_network_info_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Network Information")
        dialog.geometry("500x450")
        dialog.configure(bg=self.colors['bg_dark'])
        
        header = tk.Frame(dialog, bg=self.colors['bg_medium'])
        header.pack(fill=tk.X, padx=20, pady=20)
        
        tk.Label(header,
            text="🌐 Network Info",
            bg=self.colors['bg_medium'],
            fg=self.colors['success'],
            font=('Segoe UI', 16, 'bold')).pack(padx=20, pady=15)
        
        if self.blockchain:
            node_card = self.create_card(dialog)
            node_card.pack(fill=tk.X, padx=20, pady=(0, 15))
            
            node_content = tk.Frame(node_card, bg=self.colors['bg_medium'])
            node_content.pack(fill=tk.X, padx=20, pady=15)
            
            tk.Label(node_content,
                text="Your Node",
                bg=self.colors['bg_medium'],
                fg=self.colors['text_dim'],
                font=('Segoe UI', 9)).pack(anchor='w')
            
            tk.Label(node_content,
                text=f"{self.blockchain.my_ip}:{self.blockchain.server_port}",
                bg=self.colors['bg_medium'],
                fg=self.colors['text'],
                font=('Consolas', 12, 'bold')).pack(anchor='w', pady=(5, 0))
            
            peers_card = self.create_card(dialog)
            peers_card.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))
            
            peers_header = tk.Frame(peers_card, bg=self.colors['bg_medium'])
            peers_header.pack(fill=tk.X, padx=20, pady=(15, 10))
            
            tk.Label(peers_header,
                text="Connected Peers",
                bg=self.colors['bg_medium'],
                fg=self.colors['text_dim'],
                font=('Segoe UI', 9)).pack(side=tk.LEFT)
            
            tk.Label(peers_header,
                text=f"{len(self.blockchain.peers)} peers",
                bg=self.colors['accent'],
                fg='#000000',
                font=('Segoe UI', 8, 'bold'),
                padx=8,
                pady=3).pack(side=tk.RIGHT)
            
            if self.blockchain.peers:
                peers_list = tk.Frame(peers_card, bg=self.colors['bg_medium'])
                peers_list.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 15))
                
                for i, peer in enumerate(self.blockchain.peers, 1):
                    peer_item = tk.Frame(peers_list, bg=self.colors['bg_light'])
                    peer_item.pack(fill=tk.X, pady=3)
                    
                    tk.Label(peer_item,
                        text=f"{i}.",
                        bg=self.colors['bg_light'],
                        fg=self.colors['text_dim'],
                        font=('Segoe UI', 9),
                        width=3).pack(side=tk.LEFT, padx=(10, 5), pady=8)
                    
                    tk.Label(peer_item,
                        text=peer,
                        bg=self.colors['bg_light'],
                        fg=self.colors['text'],
                        font=('Consolas', 9)).pack(side=tk.LEFT, pady=8)
            else:
                tk.Label(peers_card,
                    text="No peers connected",
                    bg=self.colors['bg_medium'],
                    fg=self.colors['text_dim'],
                    font=('Segoe UI', 10)).pack(pady=20)
        
        close_btn = tk.Button(dialog,
            text="Close",
            bg=self.colors['bg_light'],
            fg=self.colors['text'],
            font=('Segoe UI', 10, 'bold'),
            border=0,
            cursor='hand2',
            command=dialog.destroy)
        close_btn.pack(pady=(0, 20), padx=20, fill=tk.X)
        close_btn.config(height=2)
    
    def sync_network(self):
        if not self.blockchain.peers:
            result = messagebox.askyesno("Scan Network", 
                "🔍 No peers found in your network.\n\nWould you like to scan for available peers?")
            if result:
                progress = tk.Toplevel(self.root)
                progress.title("Scanning Network")
                progress.geometry("350x150")
                progress.configure(bg=self.colors['bg_dark'])
                
                card = self.create_card(progress)
                card.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
                
                tk.Label(card,
                    text="🔍",
                    bg=self.colors['bg_medium'],
                    fg=self.colors['accent'],
                    font=('Segoe UI', 32)).pack(pady=(20, 10))
                
                tk.Label(card,
                    text="Scanning network...",
                    bg=self.colors['bg_medium'],
                    fg=self.colors['text'],
                    font=('Segoe UI', 12, 'bold')).pack()
                
                tk.Label(card,
                    text="This may take a moment",
                    bg=self.colors['bg_medium'],
                    fg=self.colors['text_dim'],
                    font=('Segoe UI', 9)).pack(pady=(5, 20))
                
                progress.update()
                
                def scan():
                    discovered = self.blockchain.scan_for_peers()
                    for peer in discovered:
                        self.blockchain.peers.add(peer)
                    progress.destroy()
                    
                    if self.blockchain.peers:
                        messagebox.showinfo("Peers Found", f"✅ Found {len(self.blockchain.peers)} peers!\n\nSyncing with network...")
                        self.blockchain.sync_with_network()
                        messagebox.showinfo("Sync Complete", "🔄 Network synchronization completed successfully!")
                    else:
                        messagebox.showwarning("No Peers", "⚠️ No peers found on the network.")
                
                threading.Thread(target=scan, daemon=True).start()
        else:
            self.blockchain.sync_with_network()
            messagebox.showinfo("Sync Complete", "🔄 Network synchronization completed successfully!")
    
    def add_peer_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Add Manual Peer")
        dialog.geometry("400x400")
        dialog.configure(bg=self.colors['bg_dark'])
        
        tk.Label(dialog,
            text="➕",
            bg=self.colors['bg_dark'],
            fg=self.colors['accent'],
            font=('Segoe UI', 32)).pack(pady=(20, 5))
        
        tk.Label(dialog,
            text="Add Manual Peer",
            bg=self.colors['bg_dark'],
            fg=self.colors['text'],
            font=('Segoe UI', 14, 'bold')).pack()
        
        form_card = self.create_card(dialog)
        form_card.pack(pady=20, padx=30, fill=tk.BOTH, expand=True)
        
        form_frame = tk.Frame(form_card, bg=self.colors['bg_medium'])
        form_frame.pack(pady=20, padx=20, fill=tk.BOTH, expand=True)
        
        tk.Label(form_frame,
            text="Peer IP Address",
            bg=self.colors['bg_medium'],
            fg=self.colors['text_dim'],
            font=('Segoe UI', 9)).pack(anchor='w', pady=(5, 5))
        
        ip_frame = tk.Frame(form_frame, bg=self.colors['bg_light'], highlightbackground=self.colors['accent'], highlightthickness=1)
        ip_frame.pack(fill=tk.X)
        
        ip_entry = tk.Entry(ip_frame,
            bg=self.colors['bg_light'],
            fg=self.colors['text'],
            font=('Consolas', 11),
            border=0,
            insertbackground=self.colors['accent'])
        ip_entry.pack(pady=12, padx=15, fill=tk.X)
        ip_entry.insert(0, "192.168.1.")
        
        def add():
            peer_ip = ip_entry.get().strip()
            if peer_ip:
                self.blockchain.add_peer(peer_ip)
                messagebox.showinfo("Success", f"✅ Added peer: {peer_ip}")
                dialog.destroy()
            else:
                messagebox.showerror("Error", "Invalid IP address!")
        
        add_btn = tk.Button(form_frame,
            text="ADD PEER",
            bg=self.colors['success'],
            fg='#000000',
            font=('Segoe UI', 11, 'bold'),
            border=0,
            cursor='hand2',
            command=add)
        add_btn.pack(fill=tk.X, pady=(15, 0))
        add_btn.config(height=2)

if __name__ == "__main__":
    root = tk.Tk()
    app = VILCoinGUI(root)
    root.mainloop()
