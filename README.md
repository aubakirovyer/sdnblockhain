# SDN Blockchain

This repository contains the implementation of an SDN (Software-Defined Networking) integrated with blockchain technology as a diploma project for CSc'25 students.

## System Requirements

- **Ubuntu 22.04 LTS** (recommended for optimal Mininet compatibility)
- Minimum 4GB RAM
- At least 20GB free disk space
- Internet connection for downloading packages and repositories

## Project Components

This project installs and integrates the following tools:

1. **Mininet**: A network emulator that creates a realistic virtual network on a single machine
2. **Docker**: Containerization platform for running isolated services
3. **Floodlight**: SDN controller (deployed as a Docker container)
4. **Containernet**: Mininet fork that allows Docker containers as network hosts
5. **Mininet-WiFi**: Extension of Mininet for wireless networks
6. **Ganache**: Local Ethereum blockchain for development and testing

## Installation

### Quick Setup

```bash
# Clone the repository
git clone https://github.com/aubakirovyer/sdnblockhain.git
cd sdnblockhain

# Make the installation script executable
chmod +x install.sh

# Run the installation script
./install.sh
```

### What the Installation Script Does

The `install.sh` script automates the installation of all required components. It performs the following tasks:

1. Updates and upgrades the system packages
2. Installs base dependencies (git, curl, ansible, nodejs, npm)
3. Clones and installs Mininet with full installation
4. Installs Docker and its components
5. Pulls the Floodlight controller Docker image
6. Clones and installs Containernet
7. Clones and installs Mininet-WiFi
8. Installs Ganache globally via NPM

All console output is logged to `install.log` for troubleshooting.

### Installation Notes

- The script will continue even if individual components fail to install
- Each major installation step is logged with clear section markers
- Check the `install.log` file for any `[ERROR]` entries after installation completes
- The script avoids re-cloning repositories if their directories already exist

## Post-Installation Verification

After installation, you can verify the components:

- **Mininet**: `sudo mn --test pingall`
- **Docker**: `docker --version` and `docker run hello-world`
- **Floodlight**: `docker images | grep floodlight`
- **Containernet**: `cd ~/containernet && sudo python3 examples/example.py`
- **Mininet-WiFi**: `cd ~/mininet-wifi && sudo python3 examples/simplewifitopology.py`
- **Ganache**: `ganache --version`

## Troubleshooting

If you encounter issues during installation:
- Check the `install.log` file for detailed error messages
- Ensure your system meets the requirements
- Make sure you have a stable internet connection
- Try running problematic installation steps manually

## License

[License information here]

## Contributors

CSc'25 students working on diploma project
