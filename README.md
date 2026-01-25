# KC Connect - REST API Server

This is the backend engine for the KC Connect ecosystem. It provides a structured, scalable API that serves community service data to mobile and web clients.

## ⚙️ Tech Stack
* **Framework:** Django 
* **API Toolkit:** Django REST Framework (DRF)
* **Database:** MySQL (Relational schema designed for service-location normalization)
* **Language:** Python

## 🛠️ Architectural Highlights
* **Decoupled Design:** Built with a "Frontend Agnostic" approach, allowing for future web or iOS clients.
* **Relational Mapping:** Implemented a one-to-many relationship between Service Providers and Locations to ensure data integrity.
* **Serializers:** Custom DRF Serializers to handle the translation of complex QuerySets into mobile-ready JSON.

## 🚀 Roadmap
* **Security:** Implementation of OAuth2/JWT authentication to protect service endpoints.
* **Testing:** Integration of a comprehensive Unit Testing suite to ensure API contract stability.
* **Automation:** Scripted data ingestion for quarterly KCPL Street Sheet updates.

## 💡 Mentorship & Contributions
I am currently the sole maintainer of this server.
* **Feedback & Mentorship:** I welcome architectural feedback or guidance on Django best practices. Please feel free to open an Issue to discuss technical improvements.
* **Pull Requests:** I am **not accepting Pull Requests** at this stage, as this project is a core part of my technical apprenticeship applications and independent learning.
