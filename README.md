# GeoSynth

**GeoSynth** is a real-time **geospatial intelligence platform** that ingests, processes, and visualizes crisis event data across the globe. GeoSynth combines **data pipelines, LLM-powered insights, and interactive visualization** to deliver live situational awareness at scale.

**Live App:** [geosynth.app](https://geosynth-five.vercel.app/)  
**Demo Video:** [Watch here](https://www.youtube.com/watch?v=2CSM4vZm1Ac&ab_channel=AkashMohan)  

## Key Features

- **Global Coverage**  
  Ingests **12,000+ crisis reports across 190+ countries**, updating in near real-time.
- **Scalable Pipelines**  
  Asynchronous ETL powered by **Celery + Redis**, processing up to **900+ reports/day**.
- **Interactive Map**  
  Sleek **Mapbox GL** frontend that visualizes events with filtering, timelines, and live updates.
- **AI-Assisted Insights**  
  Integrated with **LangChain + OpenAI** for **semantic search and natural-language Q&A** over the crisis dataset.
- **Geospatial Infrastructure**  
  Backed by **PostgreSQL + PostGIS** for geospatial queries, containerized with **Docker**, and deployed via **Railway & Vercel**.

## Tech Stack

- **Backend:** FastAPI, Celery, Redis, PostgreSQL, PostGIS  
- **AI/ML:** LangChain, OpenAI API  
- **Frontend:** Next.js, TailwindCSS, Framer Motion, Mapbox GL  
- **Infra/DevOps:** Docker, Railway, Vercel, Supabase (for PostGIS support)  

## Demo

### [Watch a short demo](https://www.youtube.com/watch?v=2CSM4vZm1Ac&ab_channel=AkashMohan) to see GeoSynth in action.  

## Roadmap
- **Enhanced Data Sources**  
  Expand beyond the ReliefWeb API and integrate additional feeds (Ex. Twitter/X, UN OCHA).
- **Advanced Analytics**  
  Add clustering, severity scoring, and **predictive modeling** to surface critical hotspots and forecast impact zones.
- **LLM-Powered Summarization**  
  Deploy automatic **multi-lingual event summaries** for each report to improve accessibility.
- **Mobile-Friendly Interface**  
  Optimize map and filters for responsive, on-the-go access.
