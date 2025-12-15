# Systemd Service Setup for keymap-util

This service file will automatically start the keyboard mapping utility on login.

```toml
[Unit]
Description=Keyboard Mapping Utility
Documentation=file:///home/nathan/FyreDE-dotfiles/KEYMAP-README.md
After=graphical-session.target
Wants=graphical-session.target

[Service]
Type=simple
# Update the device path (/dev/input/event30) and paths below to match your system
# Use: ./keymap-util.py -l to list available input devices
ExecStart=/usr/bin/sudo /opt/system/env/evdev/bin/python3 /opt/system/lib/keymap-util.py -d /dev/input/event<event ID> -c ~/.config/<path/to/config.json>
Restart=on-failure
RestartSec=2
StandardOutput=journal
StandardError=journal

# Preserve environment for Wayland
Environment="XDG_RUNTIME_DIR=%t"
Environment="WAYLAND_DISPLAY=wayland-0"
Environment="DISPLAY=:0"

[Install]
WantedBy=default.target
```

## Setup Instructions

1. **Find your input device:**
   ```bash
   ./keymap-util.py -l
   ```
   Note the device path (e.g., `/dev/input/event30`)

2. **Update the service file:**
   Edit `keymap-util.service` and update:
   - The device path (`-d /dev/input/event30`)
   - The config file path (`-c /home/nathan/FyreDE-dotfiles/keymap-config.json`)
   - The script path (`/home/nathan/FyreDE-dotfiles/keymap-util.py`)

3. **Set up sudo permissions (passwordless):**
   Create or edit `/etc/sudoers.d/keymap-util`:
   ```bash
   EDITOR=nano sudo visudo -f /etc/sudoers.d/keymap-util
   ```
   Add this line (replace `$USER` with your username):
   ```
   $USER ALL=(ALL) NOPASSWD: /opt/system/env/evdev/bin/python3 /opt/system/lib/keymap-util.py *
   ```

4. **Install the service:**
   ```bash
   # Copy to user systemd directory
   cp keymap-util.service ~/.config/systemd/user/
   
   # Reload systemd
   systemctl --user daemon-reload
   
   # Enable the service (starts on login)
   systemctl --user enable keymap-util.service
   
   # Start the service now
   systemctl --user start keymap-util.service
   ```

5. **Check service status:**
   ```bash
   systemctl --user status keymap-util.service
   ```

6. **View logs:**
   ```bash
   journalctl --user -u keymap-util.service -f
   ```

## Troubleshooting

- If the service fails to start, check logs: `journalctl --user -u keymap-util.service`
- Make sure the device path is correct and the device exists
- Verify sudo permissions work
- The service runs as your user but uses sudo to access the input device

## Alternative: Run without sudo

If you prefer not to use sudo, you can:
1. Add your user to the `input` group: `sudo usermod -aG input $USER`
2. Create a udev rule to allow access to the device
3. Modify the service to run without sudo (but this may not work for all devices)

