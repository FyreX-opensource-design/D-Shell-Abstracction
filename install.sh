sudo cp -r ./etc/xdg /etc/xdg
sudo cp -r ./system/lib /opt
sudo cp -r ./udev/* etc/udev/rules.d

cd /opt/system
mkdir env
cd ./env
sudo python3 -m venv STT
sudo ./STT/bin/pip3 install vosk
