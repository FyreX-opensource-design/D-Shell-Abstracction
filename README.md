# D-Shell-Abstracction
A Desktop shell abstraction layer using enviroment vars for customization

# Variables

$WAYBAR_THEME, WOFI_THEME

Sets the theme for various programs.

* Type: string
* Takes: absolute directory
* e.g.: `/opt/system/themes/retro`
* Notes: only takes up to the folder before applicaion config folder name. So */waybar/config and */waybar/style.css is coded into the script. i.e. the full path will be `$*_THEME/<application config>/<config files>`

$ $USB_CONNECT_SOUND, USB_DISCONNECT_SOUND

sets the sound for various functions
* Type: string
* Takes: absolute path to sound file e.g. ogg, mp3
* e.g. `/usr/share/sounds/freedesktop/stereo/device-added.oga`

$SEND_USB_NOTIFICATION
  
determines if a notification is sent or not
  
 * Type: String
 * Takes: Bool `"true"/"false"`
   
$USB_CONNECT_ICON, $USB_DISCONNECT_ICON
  
sets the icons for notifications
  
* Type: string
* Takes: absolute path to image file or icon
