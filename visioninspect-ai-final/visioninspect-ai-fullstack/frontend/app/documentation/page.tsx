"use client";
import { useState } from "react";
import Sidebar from "@/components/Sidebar";

const TABS: Record<string, { title: string; body: string[] }> = {
  architecture: {
    title: "Architecture",
    body: [
      "Backend: FastAPI + SQLAlchemy, JWT auth with bcrypt-hashed passwords, role-based access control across four roles (admin, quality_engineer, factory_supervisor, production_manager).",
      "Frontend: Next.js + TypeScript + Tailwind CSS, calling the backend over a REST API.",
      "Database: SQLite by default for local/demo use; swap DATABASE_URL for Postgres in production.",
    ],
  },
  pipeline: {
    title: "CV Pipeline",
    body: [
      "Bilateral filter for edge-preserving denoise, CLAHE for local contrast, Sobel edge detection on raw (non-normalized) magnitude, absolute threshold, morphological closing, connected-component analysis, then shape classification by solidity / extent / aspect ratio / circularity into crack, scratch, dent, or contamination.",
    ],
  },
  severity: {
    title: "Severity Scoring",
    body: [
      "Weighted formula: Size 30% + Location 25% + Type 25% + Confidence 20%.",
      "Bands: critical ≥ 80, high ≥ 60, medium ≥ 35, else low.",
      "Pass/fail/review: any critical defect → fail; any high/medium → review; otherwise pass.",
    ],
  },
  deployment: {
    title: "Deployment",
    body: [
      "Docker Compose brings up backend, frontend, and Nginx together — see deploy/docker-compose.prod.yml.",
      "Nginx reverse-proxies to the frontend and backend — see deploy/nginx/nginx.conf.",
      "Setup scripts are provided for AWS EC2 and Azure App Service — see deploy/aws_ec2_setup.sh and deploy/azure_deploy.sh. These are syntax-checked, not run against a live cloud account.",
    ],
  },
  limitations: {
    title: "Limitations",
    body: [
      "Validation numbers are computed on synthetic, generated test images with known ground truth — they prove the detection and scoring logic is internally consistent, not that it is production-accurate on real factory photos.",
      "Crack vs scratch/dent is the fuzziest classification boundary, since a deep narrow crack can look similar in shape.",
      "Accounts in this build use a simple username/password scheme suited for an internship demo; a production deployment would add password reset, email verification, and audit logging.",
    ],
  },
};

export default function DocumentationPage() {
  const [tab, setTab] = useState("architecture");
  const current = TABS[tab];

  return (
    <div className="flex">
      <Sidebar />
      <main className="flex-1 p-8 max-w-3xl">
        <h1 className="text-2xl font-bold mb-6">Documentation</h1>
        <div className="flex gap-2 mb-6 flex-wrap">
          {Object.entries(TABS).map(([key, t]) => (
            <button key={key} onClick={() => setTab(key)}
              className={`px-3 py-1.5 rounded-md text-sm ${tab === key ? "bg-amber text-bg font-semibold" : "card text-muted"}`}>
              {t.title}
            </button>
          ))}
        </div>
        <div className="card p-5">
          <h2 className="font-semibold mb-3">{current.title}</h2>
          {current.body.map((p, i) => (<p key={i} className="text-sm text-muted mb-2">{p}</p>))}
        </div>
      </main>
    </div>
  );
}
