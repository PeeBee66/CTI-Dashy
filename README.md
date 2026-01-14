![image](https://github.com/user-attachments/assets/f115bdfd-c6ab-434a-9985-339043cdeb54)

## 🚀 Overview

CTIDashy Flask is a web application that provides an interface for managing and monitoring OpenCTI data flows. It includes features for searching OpenCTI data, comparing manifests between systems, and managing file resends.

## ✨ Features

### Core Functionality
- **🔍 Doogle Search**: Search through OpenCTI data with an intuitive interface
- **📊 Manifest Comparison**: Compare manifest files between two systems
- **🔄 File Resend**: Manage and initiate file resends from backup locations
- **⚙️ Settings Management**: Configure OpenCTI connection and feature settings

## 📋 Prerequisites

- Python 3.8+
- Flask 3.1.0
- OpenCTI instance with API access
- Sufficient disk permissions for manifest and resend directories

## 🛠️ Installation

### Standard Installation

1. Clone the repository:
```bash
git clone https://github.com/PeeBee66/CTIDashy_Flask.git
cd CTIDashy_Flask
```

2. Create a virtual environment and activate it:
```bash
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
```

3. Install required packages:
```bash
pip install -r requirements.txt
```

### 🐳 Docker Installation

1. Create a `docker-compose.yml` file:
```yaml
version: '3.8'
services:
  flask_app:
    image: peebee66/mini-flask:0.2
    user: "0"
    ports:
      - "5000:5000"
    volumes:
      - /home/user/ctidashy:/app
      - /mnt/data/3.Logs:/mnt/data/3.Logs
      - /mnt/data/1.Feeds:/mnt/data/1.Feeds
      - /mnt/data/1.Feeds:/mnt/data/1.Feeds
      - /mnt/data/prod/4_re_queue:/mnt/data/prod/4_re_queue
    command: gunicorn --bind 0.0.0.0:5000 run:app
    environment:
      - OPENBLAS_NUM_THREADS=1
      - GOTO_NUM_THREADS=1
      - OMP_NUM_THREADS=1
```

2. Start the container:
```bash
docker-compose up -d
```

## ⚙️ Configuration

The application uses a JSON configuration file located at `app/settings/config.json`. Key settings include:

```json
{
    "opencti_url": "http://your-opencti-server:4000/",
    "opencti_api": "your-api-key",
    "low_side_manifest_dir": "/path/to/system1/manifests",
    "high_side_manifest_dir": "/path/to/system2/manifests",
    "resend_manifest_dir": "/path/to/resend/manifests",
    "feed_backup_dir": "/path/to/feed/backups",
    "resend_folder": "/path/to/resend/folder",
    "manifest_enabled": true,
    "resend_enabled": true
}
```

## 🚀 Running the Application

### Development Mode
```bash
python run.py
```

### Production Mode
Using Gunicorn:
```bash
gunicorn -w 4 -b 0.0.0.0:5000 run:app
```

### Docker Mode
```bash
docker-compose up -d
```

## 📁 Project Structure

```
CTIDashy_Flask/
├── config.json
├── requirements.txt
├── run.py
├── app/
│   ├── config.py          # Configuration management
│   ├── doogle.py          # Search functionality
│   ├── main.py           # Core application logic
│   ├── manifest.py       # Manifest comparison
│   ├── resend.py         # File resend management
│   ├── settings.py       # Settings management
│   ├── __init__.py
│   ├── settings/         # Configuration files
│   ├── static/           # Static assets
│   └── templates/        # HTML templates
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch:
```bash
git checkout -b feature/AmazingFeature
```
3. Commit changes:
```bash
git commit -m 'Add some AmazingFeature'
```
4. Push to branch:
```bash
git push origin feature/AmazingFeature
```
5. Open a Pull Request

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🔒 Security Considerations

- **File Permissions**: Ensure proper permissions on manifest and resend directories
- **HTTPS**: Use HTTPS for OpenCTI connections
- **API Keys**: Implement regular key rotation
- **Access Control**: Maintain appropriate access controls
- **Docker Security**: Follow container security best practices

## 🆘 Support

For support:
- Open an issue in the GitHub repository
- Contact the development team
- Check the documentation

