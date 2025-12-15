# Keyboard Mapping Utility

A utility for remapping keyboard keys with support for config-based mappings and window-specific remapping based on the focused window.

## Features

- Config-based key remapping (JSON format)
- Window-specific mappings that change based on focused window
- Uses a command like `wlrctl window list state:focused | awk '{print $1}' | sed 's/:$//'` to detect the currently focused window
- Supports both read-only mode and active remapping via uinput or dotool

## Installation

Install the required Python library (if used outside of D-Shell):

```bash
pipx install evdev
```

## Usage

Note: replace `/opt/system/lib` with script path if using elsewhere

### List Available Devices

```bash
/opt/system/lib/keymap-util.py -l
```

### Basic Usage

```bash
/opt/system/lib/keymap-util.py -d /dev/input/event30 -c /path/to/keymap-config.json
```

### Options

- `-d, --device`: Input device path (required, unless using `-l`)
- `-c, --config`: Path to JSON config file (optional)
- `-w, --window-command`: Command to get focused window (default: `./get_window.sh`)
- `-o, --output-method`: Output method: `uinput` (default) or `dotool`
- `--no-output`: Read-only mode (don't create output device)
- `-v, --verbose`: Verbose output showing all mappings
- `-l, --list`: List available input devices

## Config File Format

The config file is a JSON file with optional sections:

- `output_method`: Output method: `"uinput"` or `"dotool"` (can also be set via `-o` flag)
- `window_command`: Command to get focused window (can also be set via `-w` flag)
- `global_mappings`: Key mappings that apply to all windows
- `window_mappings`: Window-specific key mappings keyed by window name
- `command_mappings`: Global command mappings (keys execute shell commands)
- `window_command_mappings`: Window-specific command mappings

### Key Specification

Keys can be specified in two ways depending on your output method:

**For dotool output method:**
- Use key names or characters (recommended): `"i"`, `"o"`, `"a"`, `"space"`, `"enter"`, etc.
- Or use keycodes: `"23"`, `"24"`, etc.

**For uinput output method:**
- Use keycodes: `"23"`, `"24"`, `"30"`, etc.

The utility automatically converts between formats, so you can mix keycodes and names in your config. When using dotool, key names are more readable and easier to work with.

**Common key names:**
- Letters: `"a"` through `"z"`
- Numbers: `"1"` through `"0"`
- Function keys: `"f1"` through `"f24"`
- Special keys: `"space"`, `"enter"`, `"tab"`, `"backspace"`, `"escape"`, `"shift"`, `"ctrl"`, `"alt"`, `"super"`, `"up"`, `"down"`, `"left"`, `"right"`, `"home"`, `"end"`, `"pageup"`, `"pagedown"`, `"delete"`, `"insert"`

### Example Config

**Using dotool with key names and commands:**
```json
{
  "output_method": "dotool",
  "window_command": "wlrctl window list state:focused | awk '{print $1}' | sed 's/:$//'",
  "global_mappings": {
    "i": "o",
    "o": "i"
  },
  "command_mappings": {
    "f12": "notify-send 'Hello from keymap!'",
    "f11": "wofi --show drun"
  },
  "window_mappings": {
    "firefox": {
      "i": "p",
      "p": "i"
    },
    "code": {
      "a": "d",
      "d": "a"
    }
  },
  "window_command_mappings": {
    "firefox": {
      "f10": "firefox --new-tab"
    }
  }
}
```

**Using uinput with keycodes:**
```json
{
  "output_method": "uinput",
  "global_mappings": {
    "23": "24",
    "24": "23"
  },
  "command_mappings": {
    "87": "notify-send 'F11 pressed!'"
  }
}
```

**Command Mappings:**

You can map keys to execute shell commands instead of remapping to other keys. Commands are executed when the key is pressed (on keydown).

There are three ways to specify command mappings:

1. **Separate `command_mappings` section** (recommended for clarity):
   ```json
   {
     "command_mappings": {
       "f12": "notify-send 'Hello!'",
       "f11": "wofi --show drun"
     }
   }
   ```

2. **Using `cmd:` prefix in regular mappings**:
   ```json
   {
     "global_mappings": {
       "f12": "cmd:notify-send 'Hello!'"
     }
   }
   ```

3. **Window-specific command mappings**:
   ```json
   {
     "window_command_mappings": {
       "firefox": {
         "f10": "firefox --new-tab"
       }
     }
   }
   ```

Commands are executed in the background and don't block the utility. They support full shell syntax including pipes, redirects, etc.

**Note:** When a key is mapped to a command, it will NOT send the original key event. The key is consumed by the command mapping.

### Window Detection

The utility detects the focused window using a configurable command. By default, it uses `./get_window.sh` or similar (which works with wlroots compositors).

You can configure the window detection command in three ways:

1. **Via config file** (recommended):
   ```json
   {
     "window_command": "swaymsg -t get_tree | jq -r '.. | select(.focused?) | .name'"
   }
   ```

2. **Via command line**:
   ```bash
   ./keymap-util.py -d /dev/input/event30 -w "swaymsg -t get_tree | jq -r '.. | select(.focused?) | .name'"
   ```

3. **Default**: If not specified, uses `./get_window.sh` in the same directory

**Examples for different compositors:**

- **wlroots (sway, labwc, etc.)**: `wlrctl window list state:focused | awk '{print $1}' | sed 's/:$//'`
- **Sway**: `swaymsg -t get_tree | jq -r '.. | select(.focused?) | .name'`
- **Hyprland**: `hyprctl activewindow -j | jq -r '.class'`
- **River**: `riverctl list-workspaces | grep focused | awk '{print $1}'`

The command should output the window identifier/name to stdout. The utility caches the window name for 100ms to avoid excessive calls.

## Output Methods

The utility supports two output methods:

### dotool (Recommended for Wayland)

**dotool** is a Wayland-friendly tool that uses uinput under the hood but handles permissions automatically. It's simpler to use and doesn't require root.

**Installation:**
```bash
# Install from sourcehut
git clone https://git.sr.ht/~geb/dotool
cd dotool
make
sudo make install
```

See the [dotool documentation](https://git.sr.ht/~geb/dotool/tree/HEAD/doc/dotool.1.scd) for more details.

**Usage:**
```bash
./keymap-util.py -d /dev/input/event30 -c keymap-config.json -o dotool
```

Or set in config:
```json
{
  "output_method": "dotool",
  ...
}
```

**Advantages:**
- No root required (if user is in `input` group)
- Works well with Wayland compositors
- Simpler setup

### uinput (Default)

**uinput** is the traditional Linux method using Python's evdev library directly.

**Requirements:**
- User must be in `input` group, or run with root
- Python evdev library must have uinput access

**Usage:**
```bash
./keymap-util.py -d /dev/input/event30 -c keymap-config.json -o uinput
```

Or add your user to the `input` group:
```bash
sudo usermod -a -G input $USER
```

Then log out and back in.

## Finding Your Device

1. Run `evtest` and select your device number
2. Use that number in the device path: `/dev/input/event<N>`
3. Or use `./keymap-util.py -l` to list devices

## Finding Key Codes

If you need to find keycodes for the uinput method:

1. Run `evtest` on your device
2. Press keys and note the keycode numbers (e.g., `Event code 23 (KEY_I)`)
3. Use those numbers in your config

Alternatively, when using dotool, you can simply use key names like `"i"`, `"o"`, `"space"`, etc., which is much easier!

## Notes

- The utility reads events from the specified input device
- If `--no-output` is used, it only logs mappings (read-only)
- Window detection command is configurable via config file or `-w` flag
- Window name is cached for 100ms to improve performance
- Command line flags take precedence over config file settings
- **dotool** is recommended for Wayland users as it's simpler and doesn't require root
- **uinput** method requires Python evdev library and appropriate permissions


