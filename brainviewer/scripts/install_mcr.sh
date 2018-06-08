#!/bin/bash
echo "Downloading Matlab2015a runtime..."
wget http://ssd.mathworks.com/supportfiles/downloads/R2015a/deployment_files/R2015a/installers/glnxa64/MCR_R2015a_glnxa64_installer.zip -P ~/Downloads/

echo "Unpacking runtime files..."
mkdir ~/Downloads/MCR
unzip ~/Downloads/MCR_R2015a_glnxa64_installer.zip -d ~/Downloads/MCR/

echo "Installing MCR..."
cd ~/Downloads/MCR
./install -mode silent -agreeToLicense yes -destinationFolder ~/bin/mcr
