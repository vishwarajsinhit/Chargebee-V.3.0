# Chargebee-V.3.0

A comprehensive Django-based billing and payment management system integrated with Razorpay for processing payments and Chargebee for subscription management.

## 📋 Table of Contents
- [Project Overview](#project-overview)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Installation](#installation)
- [Project Structure](#project-structure)
- [Configuration](#configuration)
- [Usage](#usage)
- [Contributing](#contributing)
- [License](#license)

## 🎯 Project Overview

Chargebee-V.3.0 is an advanced billing system designed to streamline payment processing, invoice generation, and subscription management. It combines Django's robust backend framework with modern payment gateway integrations to provide a scalable solution for managing recurring payments and billing operations.

## ✨ Features

- **Payment Processing**: Seamless integration with Razorpay for secure payment transactions
- **Invoice Management**: Automated invoice generation with PDF support
- **QR Code Generation**: Built-in QR code functionality for payment methods
- **PDF Generation**: Advanced PDF generation capabilities using reportlab and xhtml2pdf
- **AWS S3 Integration**: Cloud storage support for media files
- **Database Support**: SQLite for development and PostgreSQL for production
- **REST API**: Full RESTful API for billing operations using Django REST Framework
- **Media Management**: Organized media file handling

## 🛠️ Tech Stack

### Backend
- **Framework**: Django 5.1.5
- **API**: Django REST Framework 3.15.2
- **Database**: PostgreSQL (psycopg2), SQLite
- **Payment Gateway**: Razorpay 2.0.0

### PDF & Document Processing
- **PDF Generation**: reportlab 4.4.9, xhtml2pdf 0.2.16
- **PDF Manipulation**: pypdf 6.6.2
- **PDF Signing**: pyHanko 0.32.0

### File Storage & Processing
- **AWS S3**: boto3, botocore, django-storages
- **Image Processing**: Pillow 11.0.0
- **SVG Handling**: svglib 1.6.0

### Utilities
- **QR Code**: qrcode 8.0
- **Date/Time**: python-dateutil, pytz
- **Text Processing**: Python-bidi, arabic-reshaper
- **HTTP Requests**: requests 2.32.5
- **Cryptography**: cryptography 46.0.4

### Development Dependencies
- **ASGI Server**: asgiref 3.11.1
- **File Compression**: backports.tarfile 1.2.0

## 📦 Installation

### Prerequisites
- Python 3.8 or higher
- PostgreSQL 10+ (optional, for production)
- pip package manager

### Setup Steps

1. **Clone the Repository**
   ```bash
   git clone https://github.com/vishwarajsinhit/Chargebee-V.3.0.git
   cd Chargebee-V.3.0
   ```

2. **Create a Virtual Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Database Migration**
   ```bash
   python manage.py migrate
   ```

5. **Run Development Server**
   ```bash
   python manage.py runserver
   ```

## 📁 Project Structure

```
Chargebee-V.3.0/
├── BillingSystem/          # Main Django application
├── templates/              # HTML templates
├── static/                 # Static files (CSS, JS, images)
├── media/                  # User-uploaded media files
├── manage.py               # Django management script
├── db.sqlite3              # SQLite database (development)
├── requirements.txt        # Python dependencies
├── README.md               # This file
└── gitattributes           # Git configuration
```

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the root directory with the following variables:

```bash
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/chargebee

# Razorpay
RAZORPAY_KEY_ID=your_razorpay_key_id
RAZORPAY_SECRET_KEY=your_razorpay_secret_key

# AWS S3 (Optional)
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_STORAGE_BUCKET_NAME=your_bucket_name

# Django
SECRET_KEY=your_django_secret_key
DEBUG=True  # Set to False in production
ALLOWED_HOSTS=localhost,127.0.0.1
```

## 🚀 Usage

### Running the Application

```bash
# Development server
python manage.py runserver

# Create superuser for admin panel
python manage.py createsuperuser

# Access admin panel
# Navigate to http://localhost:8000/admin/
```

### API Endpoints

The application exposes RESTful API endpoints for:
- Payment processing
- Invoice management
- Subscription handling
- Billing information retrieval

### Creating Invoices

Invoices are automatically generated with:
- PDF export capabilities
- QR codes for quick payment
- Professional formatting
- Multi-language support (Arabic, English, etc.)

## 🤝 Contributing

We welcome contributions to improve Chargebee-V.3.0! 

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 📧 Support

For support, please open an issue on the GitHub repository or contact the maintainers.

---

**Last Updated**: April 17, 2026
