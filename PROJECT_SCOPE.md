# PureteGO CRM - Project Scope & Roadmap

## 🎯 Vision
Build a robust, scalable SaaS CRM for PureteGO, initially as an MVP but designed for rapid scaling.

## 🚀 Scalability Targets
- **User Base**: Must support at least **5,000 active users** in the near future.
- **Architecture**: Modular and optimized to ensure performance under load.
- **Database**: 
  - **Dev**: Local MySQL (XAMPP) for parity with production.
  - **Prod**: MySQL on cPanel (Initial) -> Cloud SQL / Managed DB (Future Scaling).

## 🛠️ Tech Stack Strategy
- **Backend**: Python/Flask (Current).
- **Frontend**: Jinja2 Templates (MVP) -> React/Vue (Future Phase for enhanced interactivity).
- **Database**: MySQL (Optimized for relational data integrity).
- **Infrastructure**: Starting with cPanel for ease of deployment, but code should be platform-agnostic to allow migration to AWS/Google Cloud/Azure containerized environments (Docker/Kubernetes) when scaling needs hit.

## 📝 Critical Requirements
1.  **Isolation**: Keep development environment clean (no binaries/DBs in git).
2.  **Performance**: Optimize queries and asset loading for scale.
3.  **Security**: Secure authentication and data protection from day one.
