
# XBRL Generator & Validator

Een moderne web applicatie voor het genereren en valideren van XBRL bestanden uit FINREP Excel rapportages.

## 🚀 Lokale Setup

### Vereisten
- Node.js (v18 of hoger)  
- Python backend draaiend op http://192.168.2.7:5000

### Installatie

```bash
# 1. Clone de repository
git clone <YOUR_GIT_URL>
cd <YOUR_PROJECT_NAME>

# 2. Installeer dependencies
npm install

# 3. Installeer backend packages
pip install -r requirements.txt

# 4. Start de development server
npm run dev
```

De applicatie draait nu op `http://localhost:5173`

### Backend Configuratie

Deze app verbindt automatisch met je lokale Python backend:
- **Primair**: http://192.168.2.7:5000
- **Fallback**: http://localhost:5000  
- **Docker**: http://host.docker.internal:5000

Als geen backend beschikbaar is, worden demo XBRL bestanden gegenereerd.

## 📋 Functies

### ✅ XBRL Generatie
- Upload FINREP Excel (.xlsx) bestanden
- Automatische conversie naar XBRL formaat
- Real-time backend status monitoring
- Fallback naar demo generatie

### 🔍 XBRL Validatie  
- Valideer XBRL instance bestanden
- Check tegen taxonomie bestanden
- Gedetailleerde error rapportage
- Visual feedback van resultaten

## 🛠 Technologie Stack

- **Frontend**: React + TypeScript + Vite
- **Styling**: Tailwind CSS + shadcn/ui  
- **Backend**: Python Flask (extern)
- **Deployment**: Lovable Platform

## 📁 Project Structuur

```
src/
├── components/          # Herbruikbare UI componenten
│   ├── ui/             # shadcn/ui basis componenten
│   ├── BackendStatus.tsx
│   └── FileUploadZone.tsx
├── lib/
│   └── api.ts          # Backend service & API calls
├── pages/
│   ├── Index.tsx       # XBRL validatie pagina  
│   └── GenerateXBRL.tsx # XBRL generatie pagina
└── types/
    └── validation.ts   # TypeScript type definities
```

## 🔧 Development

### Backend Development
Zorg dat je Python backend draait op poort 5000 met endpoints:
- `GET /health` - Health check
- `POST /generate-xbrl` - XBRL generatie
- `POST /validate` - XBRL validatie

Installeer de benodigde Python packages met:
```bash
pip install -r requirements.txt
```

### Frontend Development
```bash
npm run dev      # Start development server
npm run build    # Build voor productie
npm run preview  # Preview productie build
```

## 🚢 Deployment

Deploy automatisch via Lovable:
1. Open je project in Lovable
2. Klik op "Publish" rechts bovenin
3. Je app is live op `yourproject.lovable.app`

## 🔗 Custom Domain

Verbind een eigen domein via Project > Settings > Domains in Lovable.

## 📞 Support

Voor hulp en vragen, check de [Lovable documentatie](https://docs.lovable.dev/) of join de [Discord community](https://discord.com/channels/1119885301872070706/1280461670979993613).
