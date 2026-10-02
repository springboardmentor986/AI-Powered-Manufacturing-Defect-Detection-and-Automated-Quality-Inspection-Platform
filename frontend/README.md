# React + Vite

This template provides a minimal setup to get React working in Vite with HMR and some ESLint rules.

Currently, two official plugins are available:

- [@vitejs/plugin-react](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react) uses [Oxc](https://oxc.rs)
- [@vitejs/plugin-react-swc](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react-swc) uses [SWC](https://swc.rs/)

## React Compiler

The React Compiler is not enabled on this template because of its impact on dev & build performances. To add it, see [this documentation](https://react.dev/learn/react-compiler/installation).

## Expanding the ESLint configuration

If you are developing a production application, we recommend using TypeScript with type-aware lint rules enabled. Check out the [TS template](https://github.com/vitejs/vite/tree/main/packages/create-vite/template-react-ts) for information on how to integrate TypeScript and [`typescript-eslint`](https://typescript-eslint.io) in your project.

# VisionInspect AI — Setup Guide
## Database
python -c "from database.connection import test_connection; test_connection()"
## Backend

Open PowerShell: and Activate virtual environment

cd D:\VisionInspectAI\backend
.\.venv\Scripts\Activate.ps1

Run FastAPI:

uvicorn main:app --reload

Backend:
http://127.0.0.1:8000

Swagger:
http://127.0.0.1:8000/docs


## Frontend

Open another terminal:

cd D:\VisionInspectAI\frontend

npm run dev

Frontend: 


http://localhost:5173


## Database

MongoDB Atlas is used as the database.

The connection string is stored in the backend environment
configuration and should not be committed to GitHub.


## Main Workflow

1. Start backend.
2. Start frontend.
3. Open frontend in browser.
4. Register a user.
5. Login.
6. Open Dashboard.
7. Select New Inspection.
8. Upload a product image.
9. Start inspection.
10. Verify the inspection record in Dashboard.