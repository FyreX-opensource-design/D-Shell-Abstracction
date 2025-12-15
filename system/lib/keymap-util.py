#!/usr/bin/env python3
"""
Keyboard mapping utility that supports config-based remapping
and window-specific mappings based on focused window.
"""

import json
import sys
import os
import subprocess
import time
import shlex
import pwd
from pathlib import Path
from typing import Dict, Optional, Any, Tuple
import argparse

try:
    from evdev import InputDevice, categorize, ecodes, UInput
except ImportError:
    print("Error: evdev library not found. Install with: pip install evdev")
    sys.exit(1)


class KeyMapper:
    def __init__(self, config_path: Optional[str] = None, device_path: Optional[str] = None, 
                 output_device: bool = True, verbose: bool = False, window_command: Optional[str] = None,
                 output_method: str = "uinput"):
        self.config_path = config_path
        self.device_path = device_path
        self.output_device = output_device
        self.verbose = verbose
        self.config = {}
        self.device = None
        self.uinput = None
        self.output_method = output_method.lower()
        self.current_window = None
        self.window_cache_time = 0
        self.window_cache_ttl = 0.1  # Cache window for 100ms
        self.window_command = window_command
        self.pressed_keys = set()  # Track pressed keys for dotool
        self.dotool_process = None  # Long-running dotool instance
        
        # Load config if provided
        if config_path:
            self.load_config(config_path)
        
        # Initialize device
        if device_path:
            self.init_device(device_path)
        
        # Initialize output device if needed
        if output_device:
            if self.output_method == "dotool":
                self.init_dotool()
            else:
                self.init_uinput()
    
    def load_config(self, config_path: str):
        """Load mapping configuration from JSON file."""
        try:
            with open(config_path, 'r') as f:
                self.config = json.load(f)
            if self.verbose:
                print(f"Loaded config from {config_path}")
            
            # Load window command from config if not set via command line
            if self.window_command is None and "window_command" in self.config:
                self.window_command = self.config["window_command"]
            
            # Load output method from config if not set via command line
            if "output_method" in self.config:
                self.output_method = self.config["output_method"].lower()
        except FileNotFoundError:
            print(f"Warning: Config file {config_path} not found. Using default mappings.")
            self.config = {}
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON in config file: {e}")
            sys.exit(1)
    
    def init_device(self, device_path: str):
        """Initialize input device."""
        try:
            self.device = InputDevice(device_path)
            # Grab the device to prevent it from sending events to the system
            # This allows us to intercept and remap keys
            try:
                self.device.grab()
                if self.verbose:
                    print(f"Grabbed device: {self.device.name} at {device_path}")
            except IOError:
                print(f"Warning: Could not grab device {device_path}. You may need root permissions.")
                print("Continuing anyway, but original keys may still be sent to the system.")
            if self.verbose:
                print(f"Opened device: {self.device.name} at {device_path}")
        except Exception as e:
            print(f"Error opening device {device_path}: {e}")
            sys.exit(1)
    
    def init_uinput(self):
        """Initialize uinput device for output."""
        try:
            # Get capabilities from input device
            if self.device:
                capabilities = self.device.capabilities()
                # Filter to only include key events
                filtered_caps = {}
                for evtype, codes in capabilities.items():
                    if evtype == ecodes.EV_KEY:
                        filtered_caps[evtype] = codes
                    elif evtype in (ecodes.EV_SYN, ecodes.EV_MSC):
                        filtered_caps[evtype] = codes
                
                self.uinput = UInput(events=filtered_caps, name="keymap-util-remapped")
                if self.verbose:
                    print("Initialized uinput output device")
            else:
                # Default keyboard capabilities
                self.uinput = UInput.from_device(self.device) if self.device else None
        except Exception as e:
            print(f"Warning: Could not initialize uinput: {e}")
            print("Continuing without output device (read-only mode)")
            self.uinput = None
    
    def init_dotool(self):
        """Initialize dotool for output (long-running instance)."""
        try:
            # Check if dotool is available
            result = subprocess.run(
                ["dotool", "--version"],
                capture_output=True,
                text=True,
                timeout=1
            )
            if result.returncode != 0:
                raise FileNotFoundError("dotool not found or not working")
            
            # Start a long-running dotool instance
            self.dotool_process = subprocess.Popen(
                ["dotool"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            if self.verbose:
                print("Initialized dotool output device")
        except FileNotFoundError:
            print("Warning: dotool not found. Install from https://git.sr.ht/~geb/dotool")
            print("Continuing without output device (read-only mode)")
            self.dotool_process = None
        except Exception as e:
            print(f"Warning: Could not initialize dotool: {e}")
            print("Continuing without output device (read-only mode)")
            self.dotool_process = None
    
    def keycode_to_dotool_name(self, key_code: int) -> Optional[str]:
        """Convert Linux keycode to dotool key name."""
        # Map common keycodes to dotool names
        # dotool supports Linux key names, XKB names (x: prefix), or keycodes (k: prefix)
        
        # Common key name mappings (case-insensitive in dotool)
        key_name_map = {
            ecodes.KEY_A: "a", ecodes.KEY_B: "b", ecodes.KEY_C: "c", ecodes.KEY_D: "d",
            ecodes.KEY_E: "e", ecodes.KEY_F: "f", ecodes.KEY_G: "g", ecodes.KEY_H: "h",
            ecodes.KEY_I: "i", ecodes.KEY_J: "j", ecodes.KEY_K: "k", ecodes.KEY_L: "l",
            ecodes.KEY_M: "m", ecodes.KEY_N: "n", ecodes.KEY_O: "o", ecodes.KEY_P: "p",
            ecodes.KEY_Q: "q", ecodes.KEY_R: "r", ecodes.KEY_S: "s", ecodes.KEY_T: "t",
            ecodes.KEY_U: "u", ecodes.KEY_V: "v", ecodes.KEY_W: "w", ecodes.KEY_X: "x",
            ecodes.KEY_Y: "y", ecodes.KEY_Z: "z",
            ecodes.KEY_1: "1", ecodes.KEY_2: "2", ecodes.KEY_3: "3", ecodes.KEY_4: "4",
            ecodes.KEY_5: "5", ecodes.KEY_6: "6", ecodes.KEY_7: "7", ecodes.KEY_8: "8",
            ecodes.KEY_9: "9", ecodes.KEY_0: "0",
            ecodes.KEY_SPACE: "space", ecodes.KEY_ENTER: "enter", ecodes.KEY_TAB: "tab",
            ecodes.KEY_BACKSPACE: "backspace", ecodes.KEY_ESC: "escape",
            ecodes.KEY_LEFTSHIFT: "shift", ecodes.KEY_RIGHTSHIFT: "shift",
            ecodes.KEY_LEFTCTRL: "ctrl", ecodes.KEY_RIGHTCTRL: "ctrl",
            ecodes.KEY_LEFTALT: "alt", ecodes.KEY_RIGHTALT: "alt",
            ecodes.KEY_LEFTMETA: "super", ecodes.KEY_RIGHTMETA: "super",
            ecodes.KEY_UP: "up", ecodes.KEY_DOWN: "down",
            ecodes.KEY_LEFT: "left", ecodes.KEY_RIGHT: "right",
            ecodes.KEY_HOME: "home", ecodes.KEY_END: "end",
            ecodes.KEY_PAGEUP: "pageup", ecodes.KEY_PAGEDOWN: "pagedown",
            ecodes.KEY_DELETE: "delete", ecodes.KEY_INSERT: "insert",
            ecodes.KEY_F1: "f1", ecodes.KEY_F2: "f2", ecodes.KEY_F3: "f3", ecodes.KEY_F4: "f4",
            ecodes.KEY_F5: "f5", ecodes.KEY_F6: "f6", ecodes.KEY_F7: "f7", ecodes.KEY_F8: "f8",
            ecodes.KEY_F9: "f9", ecodes.KEY_F10: "f10", ecodes.KEY_F11: "f11", ecodes.KEY_F12: "f12",
            ecodes.KEY_F13: "f13", ecodes.KEY_F14: "f14", ecodes.KEY_F15: "f15", ecodes.KEY_F16: "f16",
            ecodes.KEY_F17: "f17", ecodes.KEY_F18: "f18", ecodes.KEY_F19: "f19", ecodes.KEY_F20: "f20",
            ecodes.KEY_F21: "f21", ecodes.KEY_F22: "f22", ecodes.KEY_F23: "f23", ecodes.KEY_F24: "f24",
        }
        
        if key_code in key_name_map:
            return key_name_map[key_code]
        
        # Fallback to keycode format (k: prefix)
        return f"k:{key_code}"
    
    def name_to_keycode(self, key_name: str) -> Optional[int]:
        """Convert key name or character to Linux keycode."""
        # Try to find in ecodes.KEY dict (case-insensitive)
        key_name_upper = key_name.upper()
        if key_name_upper.startswith("KEY_"):
            key_name_upper = key_name_upper
        else:
            key_name_upper = f"KEY_{key_name_upper}"
        
        # Search in ecodes.KEY
        for code, name in ecodes.KEY.items():
            if name == key_name_upper:
                return code
        
        # Try single character (a-z, 0-9)
        if len(key_name) == 1:
            char = key_name.lower()
            char_map = {
                'a': ecodes.KEY_A, 'b': ecodes.KEY_B, 'c': ecodes.KEY_C, 'd': ecodes.KEY_D,
                'e': ecodes.KEY_E, 'f': ecodes.KEY_F, 'g': ecodes.KEY_G, 'h': ecodes.KEY_H,
                'i': ecodes.KEY_I, 'j': ecodes.KEY_J, 'k': ecodes.KEY_K, 'l': ecodes.KEY_L,
                'm': ecodes.KEY_M, 'n': ecodes.KEY_N, 'o': ecodes.KEY_O, 'p': ecodes.KEY_P,
                'q': ecodes.KEY_Q, 'r': ecodes.KEY_R, 's': ecodes.KEY_S, 't': ecodes.KEY_T,
                'u': ecodes.KEY_U, 'v': ecodes.KEY_V, 'w': ecodes.KEY_W, 'x': ecodes.KEY_X,
                'y': ecodes.KEY_Y, 'z': ecodes.KEY_Z,
                '1': ecodes.KEY_1, '2': ecodes.KEY_2, '3': ecodes.KEY_3, '4': ecodes.KEY_4,
                '5': ecodes.KEY_5, '6': ecodes.KEY_6, '7': ecodes.KEY_7, '8': ecodes.KEY_8,
                '9': ecodes.KEY_9, '0': ecodes.KEY_0,
            }
            if char in char_map:
                return char_map[char]
        
        # Try common key names
        name_map = {
            'space': ecodes.KEY_SPACE, 'enter': ecodes.KEY_ENTER, 'tab': ecodes.KEY_TAB,
            'backspace': ecodes.KEY_BACKSPACE, 'escape': ecodes.KEY_ESC, 'esc': ecodes.KEY_ESC,
            'shift': ecodes.KEY_LEFTSHIFT, 'ctrl': ecodes.KEY_LEFTCTRL, 'control': ecodes.KEY_LEFTCTRL,
            'alt': ecodes.KEY_LEFTALT, 'super': ecodes.KEY_LEFTMETA, 'meta': ecodes.KEY_LEFTMETA,
            'up': ecodes.KEY_UP, 'down': ecodes.KEY_DOWN, 'left': ecodes.KEY_LEFT, 'right': ecodes.KEY_RIGHT,
            'home': ecodes.KEY_HOME, 'end': ecodes.KEY_END,
            'pageup': ecodes.KEY_PAGEUP, 'pagedown': ecodes.KEY_PAGEDOWN,
            'delete': ecodes.KEY_DELETE, 'insert': ecodes.KEY_INSERT,
            'f1': ecodes.KEY_F1, 'f2': ecodes.KEY_F2, 'f3': ecodes.KEY_F3, 'f4': ecodes.KEY_F4,
            'f5': ecodes.KEY_F5, 'f6': ecodes.KEY_F6, 'f7': ecodes.KEY_F7, 'f8': ecodes.KEY_F8,
            'f9': ecodes.KEY_F9, 'f10': ecodes.KEY_F10, 'f11': ecodes.KEY_F11, 'f12': ecodes.KEY_F12,
            'f13': ecodes.KEY_F13, 'f14': ecodes.KEY_F14, 'f15': ecodes.KEY_F15, 'f16': ecodes.KEY_F16,
            'f17': ecodes.KEY_F17, 'f18': ecodes.KEY_F18, 'f19': ecodes.KEY_F19, 'f20': ecodes.KEY_F20,
            'f21': ecodes.KEY_F21, 'f22': ecodes.KEY_F22, 'f23': ecodes.KEY_F23, 'f24': ecodes.KEY_F24,
        }
        if key_name.lower() in name_map:
            return name_map[key_name.lower()]
        
        return None
    
    def normalize_config_key(self, key: str) -> Tuple[Optional[int], Optional[str]]:
        """Normalize a config key to both keycode and name format.
        Returns (keycode, name) tuple. Either can be None if conversion fails."""
        # Try as key name/character first (for both single and multi-character names)
        # This ensures "1" means KEY_1, not keycode 1 (KEY_ESC)
        # This also handles letters, function keys, and special keys
        keycode = self.name_to_keycode(key)
        if keycode is not None:
            name = self.keycode_to_dotool_name(keycode)
            return (keycode, name)
        
        # If name lookup failed, try as keycode (numeric string)
        # This allows users to specify explicit keycodes if needed
        # Note: For single-digit strings, this will only be reached if name_to_keycode
        # failed, which shouldn't happen for "0"-"9", but could for other single chars
        try:
            keycode = int(key)
            name = self.keycode_to_dotool_name(keycode)
            return (keycode, name)
        except ValueError:
            pass
        
        return (None, None)
    
    def send_dotool_key(self, key_name: str, value: int):
        """Send key event via dotool using key name."""
        if not self.dotool_process or not key_name:
            return
        
        try:
            if value == 1:  # Key press
                if key_name not in self.pressed_keys:
                    self.dotool_process.stdin.write(f"keydown {key_name}\n")
                    self.dotool_process.stdin.flush()
                    self.pressed_keys.add(key_name)
            elif value == 0:  # Key release
                if key_name in self.pressed_keys:
                    self.dotool_process.stdin.write(f"keyup {key_name}\n")
                    self.dotool_process.stdin.flush()
                    self.pressed_keys.discard(key_name)
            # value == 2 is key repeat, we can ignore it or treat as press
        except (BrokenPipeError, OSError) as e:
            if self.verbose:
                print(f"Warning: dotool communication error: {e}")
            self.dotool_process = None
    
    def resolve_window_command_path(self, cmd_path: str) -> str:
        """Resolve a window command path to an absolute path."""
        # If it's already absolute, return as-is
        if os.path.isabs(cmd_path):
            return cmd_path
        
        # If it doesn't look like a file path (no slashes, no extension), 
        # assume it's a command in PATH
        if '/' not in cmd_path and not cmd_path.startswith('./') and not cmd_path.startswith('../'):
            # Check if it's a script file (has extension)
            if not (cmd_path.endswith('.sh') or cmd_path.endswith('.py') or 
                    cmd_path.endswith('.pl') or cmd_path.endswith('.rb')):
                return cmd_path  # Probably a command in PATH
        
        # Try to resolve relative to config file directory first
        if self.config_path:
            config_dir = Path(self.config_path).parent.resolve()
            config_relative = config_dir / cmd_path
            if config_relative.exists() and (config_relative.is_file() or config_relative.is_symlink()):
                return str(config_relative.resolve())
        
        # Try relative to script directory
        script_dir = Path(__file__).parent.resolve()
        script_relative = script_dir / cmd_path
        if script_relative.exists() and (script_relative.is_file() or script_relative.is_symlink()):
            return str(script_relative.resolve())
        
        # Try relative to current working directory
        cwd_relative = Path(cmd_path).resolve()
        if cwd_relative.exists() and (cwd_relative.is_file() or cwd_relative.is_symlink()):
            return str(cwd_relative)
        
        # If not found, return original (might be a command in PATH or will error later)
        return cmd_path
    
    def get_focused_window(self) -> Optional[str]:
        """Get the currently focused window using the configured command."""
        cache_time = time.time()
        if cache_time - self.window_cache_time < self.window_cache_ttl:
            return self.current_window
        
        # Determine which command to use
        use_shell = False
        if self.window_command:
            # Use configured command (can be a string or list)
            if isinstance(self.window_command, str):
                # Check if command contains shell operators (pipes, redirects, etc.)
                # If so, we need to run it in a shell
                if '|' in self.window_command or '>' in self.window_command or '<' in self.window_command or '&' in self.window_command or ';' in self.window_command:
                    use_shell = True
                    cmd = self.window_command
                else:
                    # If it's a string, split by spaces but respect quotes
                    cmd = shlex.split(self.window_command)
                    # Resolve the first element (the script/command) if it looks like a file path
                    if cmd and not os.path.isabs(cmd[0]):
                        # Check if it looks like a relative file path
                        if (cmd[0].startswith('./') or cmd[0].startswith('../') or 
                            '/' in cmd[0] or cmd[0].endswith(('.sh', '.py', '.pl', '.rb', '.bash'))):
                            cmd[0] = self.resolve_window_command_path(cmd[0])
            else:
                # If it's already a list, use it directly
                cmd = list(self.window_command)  # Make a copy to avoid modifying original
                # Resolve the first element if it looks like a file path
                if cmd and not os.path.isabs(cmd[0]):
                    # Check if it looks like a relative file path
                    if (cmd[0].startswith('./') or cmd[0].startswith('../') or 
                        '/' in cmd[0] or cmd[0].endswith(('.sh', '.py', '.pl', '.rb', '.bash'))):
                        cmd[0] = self.resolve_window_command_path(cmd[0])
        else:
            # Default: use get_window.sh in the same directory
            script_path = Path(__file__).parent / "get_window.sh"
            cmd = [str(script_path.resolve())]
        
        # Check if we're running as root and need to execute as original user
        original_user = None
        if os.geteuid() == 0:
            original_user = self.get_original_user()
        
        try:
            if original_user:
                # Run as the original user with proper environment
                user_env = self.get_user_environment(original_user)
                
                if self.verbose:
                    print(f"Running window detection as user: {original_user}")
                
                # Build environment export string
                env_exports = ' '.join([f'export {k}="{v}";' for k, v in user_env.items()])
                
                # Build the command
                if use_shell:
                    # Command is already a string, wrap it with environment
                    full_command = f'{env_exports} {cmd}'
                else:
                    # Command is a list, convert to string
                    cmd_str = ' '.join([shlex.quote(str(c)) for c in cmd])
                    full_command = f'{env_exports} {cmd_str}'
                
                # Use runuser (preferred) or su to run as the user
                try:
                    result = subprocess.run(
                        ['runuser', '-l', original_user, '-c', full_command],
                        capture_output=True,
                        text=True,
                        timeout=0.1
                    )
                except FileNotFoundError:
                    # Fallback to su if runuser not available
                    result = subprocess.run(
                        ['su', '-', original_user, '-c', full_command],
                        capture_output=True,
                        text=True,
                        timeout=0.1
                    )
            else:
                # Not running as root, execute normally
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=0.1,
                    shell=use_shell
                )
            
            if result.returncode == 0:
                window = result.stdout.strip()
                # Also strip any trailing/leading whitespace that might interfere
                window = window.strip()
                self.current_window = window if window else None
                self.window_cache_time = cache_time
                if self.verbose:
                    if self.current_window:
                        print(f"Detected window: '{self.current_window}' (length: {len(self.current_window)})")
                    else:
                        print(f"Window detection returned empty string (stderr: {result.stderr})")
                return self.current_window
            else:
                if self.verbose:
                    print(f"Window detection command failed with return code {result.returncode}")
                    print(f"  stdout: {result.stdout}")
                    print(f"  stderr: {result.stderr}")
        except subprocess.TimeoutExpired:
            if self.verbose:
                print("Warning: Window detection command timed out")
        except FileNotFoundError:
            if self.verbose:
                cmd_str = cmd if isinstance(cmd, str) else cmd[0] if cmd else "unknown"
                print(f"Warning: Window detection command not found: {cmd_str}")
        except Exception as e:
            if self.verbose:
                print(f"Warning: Could not get focused window: {e}")
        
        return self.current_window
    
    def is_command_mapping(self, mapped_value: str) -> bool:
        """Check if a mapped value is a command (starts with 'cmd:' or is in command_mappings)."""
        if isinstance(mapped_value, str):
            return mapped_value.startswith("cmd:") or mapped_value.startswith("CMD:")
        return False
    
    def get_command_from_mapping(self, mapped_value: str) -> Optional[str]:
        """Extract command from mapping value."""
        if isinstance(mapped_value, str):
            if mapped_value.startswith("cmd:"):
                return mapped_value[4:].strip()
            elif mapped_value.startswith("CMD:"):
                return mapped_value[4:].strip()
        return None
    
    def get_original_user(self) -> Optional[str]:
        """Get the original user (if running via sudo)."""
        # Check for SUDO_USER first (most common)
        sudo_user = os.environ.get('SUDO_USER')
        if sudo_user:
            return sudo_user
        
        # Check for PKEXEC_UID (polkit)
        pkexec_uid = os.environ.get('PKEXEC_UID')
        if pkexec_uid:
            try:
                return pwd.getpwuid(int(pkexec_uid)).pw_name
            except (ValueError, KeyError):
                pass
        
        # If we're root, try to get the first non-root user with a session
        if os.geteuid() == 0:
            # Try to find a user with a display session
            for env_var in ['XDG_RUNTIME_DIR', 'WAYLAND_DISPLAY', 'DISPLAY']:
                runtime_dir = os.environ.get(env_var)
                if runtime_dir:
                    # Try to extract user from path like /run/user/1000
                    if '/run/user/' in str(runtime_dir):
                        try:
                            uid = int(str(runtime_dir).split('/run/user/')[1].split('/')[0])
                            return pwd.getpwuid(uid).pw_name
                        except (ValueError, IndexError, KeyError):
                            pass
        
        return None
    
    def get_user_environment(self, username: str) -> Dict[str, str]:
        """Get environment variables for a user."""
        env = {}
        
        # Get user's home directory
        try:
            user_info = pwd.getpwnam(username)
            env['HOME'] = user_info.pw_dir
            env['USER'] = username
            env['USERNAME'] = username
        except KeyError:
            return env
        
        # Try to get XDG_RUNTIME_DIR (usually /run/user/UID)
        try:
            xdg_runtime = f"/run/user/{user_info.pw_uid}"
            if os.path.exists(xdg_runtime):
                env['XDG_RUNTIME_DIR'] = xdg_runtime
        except:
            pass
        
        # Copy important environment variables from current process if they exist
        # These are often set in the root session but should be available to the user
        for var in ['WAYLAND_DISPLAY', 'DISPLAY', 'XDG_SESSION_TYPE', 'XDG_CURRENT_DESKTOP']:
            if var in os.environ:
                env[var] = os.environ[var]
        
        # Also try to get WAYLAND_DISPLAY from the user's runtime dir
        if 'XDG_RUNTIME_DIR' in env:
            wayland_socket = os.path.join(env['XDG_RUNTIME_DIR'], 'wayland-0')
            if os.path.exists(wayland_socket):
                env['WAYLAND_DISPLAY'] = 'wayland-0'
        
        return env
    
    def execute_command(self, command: str):
        """Execute a shell command as the original user (if running as root)."""
        try:
            if self.verbose:
                print(f"Executing command: {command}")
            
            # Check if we're running as root and need to execute as original user
            original_user = None
            if os.geteuid() == 0:
                original_user = self.get_original_user()
            
            if original_user:
                # Execute as the original user with proper environment
                user_env = self.get_user_environment(original_user)
                
                if self.verbose:
                    print(f"Running as user: {original_user}")
                
                # Build environment export string
                env_exports = ' '.join([f'export {k}="{v}";' for k, v in user_env.items()])
                full_command = f'{env_exports} {command}'
                
                # Use runuser (preferred) or su to run as the user
                # runuser is cleaner when already root
                try:
                    # Try runuser first (available on most Linux systems)
                    # -l makes it a login shell which loads user's profile
                    subprocess.Popen(
                        ['runuser', '-l', original_user, '-c', full_command],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        start_new_session=True  # Detach from parent process
                    )
                except FileNotFoundError:
                    # Fallback to su if runuser not available
                    subprocess.Popen(
                        ['su', '-', original_user, '-c', full_command],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        start_new_session=True  # Detach from parent process
                    )
            else:
                # Not running as root, execute normally
                subprocess.Popen(
                    command,
                    shell=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True  # Detach from parent process
                )
        except Exception as e:
            if self.verbose:
                print(f"Error executing command '{command}': {e}")
    
    def get_mapping(self, key_code: int):
        """Get the mapped key for a given key, considering window-specific mappings.
        Returns keycode for uinput, key name for dotool, or 'COMMAND' if it's a command mapping."""
        window = self.get_focused_window()
        key_name = self.keycode_to_dotool_name(key_code)
        
        # Build lookup keys (both keycode string and key name)
        lookup_keys = [str(key_code)]
        if key_name:
            lookup_keys.extend([key_name, key_name.lower(), key_name.upper()])
        
        # Check for window-specific command mappings first
        if self.verbose:
            print(f"get_mapping: key_code={key_code}, key_name={key_name}, window='{window}'")
        
        if window and "window_command_mappings" in self.config:
            window_cmd_maps = self.config["window_command_mappings"]
            # Try exact match first, then case-insensitive match, then substring match
            window_key = None
            if window in window_cmd_maps:
                window_key = window
            else:
                # Try case-insensitive exact match
                for w in window_cmd_maps.keys():
                    if w.lower() == window.lower():
                        window_key = w
                        break
                
                # If still no match, try substring match (e.g., "krita" matches "org.kde.krita")
                if window_key is None:
                    window_lower = window.lower()
                    for w in window_cmd_maps.keys():
                        if w.lower() in window_lower or window_lower in w.lower():
                            window_key = w
                            if self.verbose:
                                print(f"Window match (substring): '{window}' matched '{w}'")
                            break
                
                if window_key is None and self.verbose:
                    print(f"Window not matched: '{window}' (available: {list(window_cmd_maps.keys())})")
            
            if window_key:
                if self.verbose:
                    print(f"Checking window '{window_key}' mappings. lookup_keys: {lookup_keys}, available keys: {list(window_cmd_maps[window_key].keys())}")
                
                # Try direct lookup, but verify the match is correct by normalizing
                # This prevents "4" (keycode string) from matching config "4" (KEY_4, keycode 5)
                for lookup_key in lookup_keys:
                    if lookup_key in window_cmd_maps[window_key]:
                        # Verify this is the correct match by normalizing the config key
                        normalized_keycode, normalized_name = self.normalize_config_key(lookup_key)
                        # Only use this match if the normalized keycode matches what we pressed
                        if normalized_keycode == key_code:
                            mapped = window_cmd_maps[window_key][lookup_key]
                            if self.verbose:
                                print(f"Window-specific command mapping: {key_code} ({key_name}) -> {mapped} (window: {window_key})")
                            return ("COMMAND", mapped)
                
                if self.verbose:
                    print(f"Direct lookup failed, trying normalization for keys: {list(window_cmd_maps[window_key].keys())}")
                
                # Also try normalizing config keys to handle cases where user wrote keycode
                # but meant key name (e.g., "2" in config when they meant KEY_1 which is keycode 2)
                for config_key in list(window_cmd_maps[window_key].keys()):
                    normalized_keycode, normalized_name = self.normalize_config_key(config_key)
                    if self.verbose:
                        print(f"  Normalizing config key '{config_key}': keycode={normalized_keycode}, name={normalized_name}, current key_code={key_code}")
                    # Check if normalized keycode matches our key (most reliable)
                    if normalized_keycode == key_code:
                        mapped = window_cmd_maps[window_key][config_key]
                        if self.verbose:
                            print(f"Window-specific command mapping: {key_code} ({key_name}) -> {mapped} (window: {window_key}, matched via normalized key '{config_key}')")
                        return ("COMMAND", mapped)
                
                if self.verbose:
                    print(f"No match found in window '{window_key}' mappings")
        
        # Check for global command mappings
        if "command_mappings" in self.config:
            cmd_maps = self.config["command_mappings"]
            # Try direct lookup, but verify the match is correct by normalizing
            for lookup_key in lookup_keys:
                if lookup_key in cmd_maps:
                    # Verify this is the correct match by normalizing the config key
                    normalized_keycode, normalized_name = self.normalize_config_key(lookup_key)
                    # Only use this match if the normalized keycode matches what we pressed
                    if normalized_keycode == key_code:
                        mapped = cmd_maps[lookup_key]
                        if self.verbose:
                            print(f"Global command mapping: {key_code} ({key_name}) -> {mapped}")
                        return ("COMMAND", mapped)
            
            # Also try normalizing config keys to handle cases where user wrote keycode
            # but meant key name (e.g., "2" in config when they meant KEY_1 which is keycode 2)
            for config_key in list(cmd_maps.keys()):
                normalized_keycode, normalized_name = self.normalize_config_key(config_key)
                # Check if normalized keycode matches our key (most reliable)
                if normalized_keycode == key_code:
                    mapped = cmd_maps[config_key]
                    if self.verbose:
                        print(f"Global command mapping: {key_code} ({key_name}) -> {mapped} (matched via normalized key '{config_key}')")
                    return ("COMMAND", mapped)
        
        # Check for window-specific key mappings
        if window and "window_mappings" in self.config:
            window_maps = self.config["window_mappings"]
            # Try exact match first, then case-insensitive match, then substring match
            window_key = None
            if window in window_maps:
                window_key = window
            else:
                # Try case-insensitive exact match
                for w in window_maps.keys():
                    if w.lower() == window.lower():
                        window_key = w
                        break
                
                # If still no match, try substring match (e.g., "krita" matches "org.kde.krita")
                if window_key is None:
                    window_lower = window.lower()
                    for w in window_maps.keys():
                        if w.lower() in window_lower or window_lower in w.lower():
                            window_key = w
                            if self.verbose:
                                print(f"Window match (substring): '{window}' matched '{w}'")
                            break
                
                if window_key is None and self.verbose:
                    print(f"Window not matched: '{window}' (available: {list(window_maps.keys())})")
            
            if window_key:
                # Try direct lookup, but verify the match is correct by normalizing
                for lookup_key in lookup_keys:
                    if lookup_key in window_maps[window_key]:
                        # Verify this is the correct match by normalizing the config key
                        normalized_keycode, normalized_name = self.normalize_config_key(lookup_key)
                        # Only use this match if the normalized keycode matches what we pressed
                        if normalized_keycode == key_code:
                            mapped = window_maps[window_key][lookup_key]
                            
                            # Check if it's a command (cmd: prefix)
                            if self.is_command_mapping(mapped):
                                cmd = self.get_command_from_mapping(mapped)
                                if cmd:
                                    if self.verbose:
                                        print(f"Window-specific command mapping: {key_code} ({key_name}) -> {cmd} (window: {window_key})")
                                    return ("COMMAND", cmd)
                            
                            if self.verbose:
                                print(f"Window-specific mapping: {key_code} ({key_name}) -> {mapped} (window: {window_key})")
                            
                            # Convert mapped value based on output method
                            if self.output_method == "dotool":
                                # Return as-is if it's already a name, otherwise convert
                                mapped_keycode, mapped_name = self.normalize_config_key(mapped)
                                return mapped_name if mapped_name else mapped
                            else:
                                # Return keycode
                                mapped_keycode, _ = self.normalize_config_key(mapped)
                                return mapped_keycode if mapped_keycode else int(mapped)
                
                # Also try normalizing config keys to handle cases where user wrote keycode
                # but meant key name (e.g., "5" in config when they meant KEY_4 which is keycode 5)
                for config_key in list(window_maps[window_key].keys()):
                    normalized_keycode, normalized_name = self.normalize_config_key(config_key)
                    # Check if normalized keycode matches our key (most reliable)
                    if normalized_keycode == key_code:
                        mapped = window_maps[window_key][config_key]
                        
                        # Check if it's a command (cmd: prefix)
                        if self.is_command_mapping(mapped):
                            cmd = self.get_command_from_mapping(mapped)
                            if cmd:
                                if self.verbose:
                                    print(f"Window-specific command mapping: {key_code} ({key_name}) -> {cmd} (window: {window_key}, matched via normalized key '{config_key}')")
                                return ("COMMAND", cmd)
                        
                        if self.verbose:
                            print(f"Window-specific mapping: {key_code} ({key_name}) -> {mapped} (window: {window_key}, matched via normalized key '{config_key}')")
                        
                        # Convert mapped value based on output method
                        if self.output_method == "dotool":
                            mapped_keycode, mapped_name = self.normalize_config_key(mapped)
                            return mapped_name if mapped_name else mapped
                        else:
                            mapped_keycode, _ = self.normalize_config_key(mapped)
                            return mapped_keycode if mapped_keycode else int(mapped)
        
        # Check for global key mappings
        if "global_mappings" in self.config:
            global_maps = self.config["global_mappings"]
            # Try direct lookup, but verify the match is correct by normalizing
            for lookup_key in lookup_keys:
                if lookup_key in global_maps:
                    # Verify this is the correct match by normalizing the config key
                    normalized_keycode, normalized_name = self.normalize_config_key(lookup_key)
                    # Only use this match if the normalized keycode matches what we pressed
                    if normalized_keycode == key_code:
                        mapped = global_maps[lookup_key]
                        
                        # Check if it's a command (cmd: prefix)
                        if self.is_command_mapping(mapped):
                            cmd = self.get_command_from_mapping(mapped)
                            if cmd:
                                if self.verbose:
                                    print(f"Global command mapping: {key_code} ({key_name}) -> {cmd}")
                                return ("COMMAND", cmd)
                        
                        if self.verbose:
                            print(f"Global mapping: {key_code} ({key_name}) -> {mapped}")
                        
                        # Convert mapped value based on output method
                        if self.output_method == "dotool":
                            # Return as-is if it's already a name, otherwise convert
                            mapped_keycode, mapped_name = self.normalize_config_key(mapped)
                            return mapped_name if mapped_name else mapped
                        else:
                            # Return keycode
                            mapped_keycode, _ = self.normalize_config_key(mapped)
                            return mapped_keycode if mapped_keycode else int(mapped)
            
            # Also try normalizing config keys to handle cases where user wrote keycode
            # but meant key name
            for config_key in list(global_maps.keys()):
                normalized_keycode, normalized_name = self.normalize_config_key(config_key)
                # Check if normalized keycode matches our key (most reliable)
                if normalized_keycode == key_code:
                    mapped = global_maps[config_key]
                    
                    # Check if it's a command (cmd: prefix)
                    if self.is_command_mapping(mapped):
                        cmd = self.get_command_from_mapping(mapped)
                        if cmd:
                            if self.verbose:
                                print(f"Global command mapping: {key_code} ({key_name}) -> {cmd} (matched via normalized key '{config_key}')")
                            return ("COMMAND", cmd)
                    
                    if self.verbose:
                        print(f"Global mapping: {key_code} ({key_name}) -> {mapped} (matched via normalized key '{config_key}')")
                    
                    # Convert mapped value based on output method
                    if self.output_method == "dotool":
                        mapped_keycode, mapped_name = self.normalize_config_key(mapped)
                        return mapped_name if mapped_name else mapped
                    else:
                        mapped_keycode, _ = self.normalize_config_key(mapped)
                        return mapped_keycode if mapped_keycode else int(mapped)
        
        # No mapping found, return original
        return None
    
    def process_event(self, event):
        """Process a single input event."""
        if event.type == ecodes.EV_KEY:
            key_event = categorize(event)
            key_code = event.code
            key_name = self.keycode_to_dotool_name(key_code)
            
            if self.verbose and event.value == 1:  # Only log on key press
                print(f"Key event: code={key_code}, name={key_name}, value={event.value}")
            
            mapped = self.get_mapping(key_code)
            
            # Check if this is a command mapping
            if isinstance(mapped, tuple) and mapped[0] == "COMMAND":
                # Execute command on key press only (value == 1)
                if event.value == 1:
                    self.execute_command(mapped[1])
                # Don't send any key event for command mappings
                return
            
            # Determine which key to send
            if mapped is not None:
                output_key = mapped
            else:
                # No mapping, use original
                if self.output_method == "dotool":
                    output_key = self.keycode_to_dotool_name(key_code)
                else:
                    output_key = key_code
            
            if mapped is not None and self.verbose:
                if self.output_method == "dotool":
                    print(f"Mapped: {key_code} ({self.keycode_to_dotool_name(key_code)}) -> {output_key}, value: {event.value}")
                else:
                    key_name = ecodes.KEY[mapped] if mapped in ecodes.KEY else f"KEY_{mapped}"
                    print(f"Mapped: {key_code} -> {mapped} ({key_name}), value: {event.value}")
            
            # Send via appropriate output method
            if self.output_method == "dotool" and self.dotool_process and output_key:
                self.send_dotool_key(output_key, event.value)
            elif self.uinput and isinstance(output_key, int):
                self.uinput.write(ecodes.EV_KEY, output_key, event.value)
                self.uinput.syn()
        else:
            # Pass through non-key events (only for uinput)
            if self.uinput:
                self.uinput.write(event.type, event.code, event.value)
                if event.type == ecodes.EV_SYN:
                    self.uinput.syn()
    
    def run(self):
        """Main event loop."""
        if not self.device:
            print("Error: No input device specified")
            sys.exit(1)
        
        print(f"Listening to {self.device.name}...")
        if self.output_method == "dotool" and self.dotool_process:
            print("Output method: dotool - remapped keys will be sent")
        elif self.uinput:
            print("Output method: uinput - remapped keys will be sent")
        else:
            print("Read-only mode - no output device")
        print("Press Ctrl+C to exit\n")
        
        try:
            for event in self.device.read_loop():
                self.process_event(event)
        except KeyboardInterrupt:
            print("\nExiting...")
        finally:
            if self.dotool_process:
                try:
                    self.dotool_process.stdin.close()
                    self.dotool_process.terminate()
                    self.dotool_process.wait(timeout=1)
                except:
                    pass
            if self.uinput:
                self.uinput.close()
            if self.device:
                self.device.close()


def list_devices():
    """List available input devices."""
    print("Available input devices:")
    print("-" * 60)
    for path in Path("/dev/input").glob("event*"):
        try:
            device = InputDevice(path)
            print(f"{path.name:12} - {device.name}")
            device.close()
        except:
            pass


def main():
    parser = argparse.ArgumentParser(
        description="Keyboard mapping utility with config and window-specific mappings"
    )
    parser.add_argument(
        "-d", "--device",
        help="Input device path (e.g., /dev/input/event30)"
    )
    parser.add_argument(
        "-c", "--config",
        help="Config file path (JSON format)"
    )
    parser.add_argument(
        "--no-output",
        action="store_true",
        help="Read-only mode (don't create output device)"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Verbose output"
    )
    parser.add_argument(
        "-l", "--list",
        action="store_true",
        help="List available input devices"
    )
    parser.add_argument(
        "-w", "--window-command",
        help="Command to get focused window (default: ./get_window.sh). "
             "Can be a command string or path to script. "
             "Can also be set in config file as 'window_command'."
    )
    parser.add_argument(
        "-o", "--output-method",
        choices=["uinput", "dotool"],
        default="uinput",
        help="Output method: 'uinput' (default) or 'dotool'. "
             "dotool is simpler for Wayland and doesn't require root. "
             "Can also be set in config file as 'output_method'."
    )
    
    args = parser.parse_args()
    
    if args.list:
        list_devices()
        return
    
    if not args.device:
        print("Error: Device path required. Use -d/--device or -l/--list to see available devices.")
        sys.exit(1)
    
    mapper = KeyMapper(
        config_path=args.config,
        device_path=args.device,
        output_device=not args.no_output,
        verbose=args.verbose,
        window_command=args.window_command,
        output_method=args.output_method
    )
    
    mapper.run()


if __name__ == "__main__":
    main()

