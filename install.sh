# Create destination directories
sudo mkdir -p /etc/xdg
sudo mkdir -p /opt/system
sudo mkdir -p /etc/udev/rules.d

# Copy files to correct locations
sudo cp -r ./etc/xdg/* /etc/xdg/
sudo cp -r ./system/lib /opt/system/
sudo cp -r ./system/default /opt/system/ 2>/dev/null || true
sudo cp -r ./system/apps /opt/system/ 2>/dev/null || true

# Ensure all scripts are executable and readable by users (755 = rwxr-xr-x)
sudo find /opt/system/lib -type f -name "*.sh" -exec chmod 755 {} \;

# Copy udev rules and reload
sudo cp -r ./udev/* /etc/udev/rules.d/
sudo udevadm control --reload-rules

# Install systemd user services
if [ -d "./systemd/user" ]; then
    sudo mkdir -p /usr/lib/systemd/user
fi
sudo cp ./systemd/user/*.service /usr/lib/systemd/user/
sudo systemctl daemon-reload

cd /opt/system
mkdir env
cd ./env
sudo python3 -m venv STT
sudo ./STT/bin/pip3 install vosk
