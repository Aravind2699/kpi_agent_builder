import axios from "axios";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000/api";

const client = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: false,
  headers: {
    "Content-Type": "application/json",
  },
});

export const generateQuestions = (kpi_name) => client.post("/generate-questions/", { kpi_name });
export const buildIntent = (kpi_name, metric_type, answers) =>
  client.post("/build-intent/", { kpi_name, metric_type, answers });
export const validateIntent = (intent) => client.post("/validate-intent/", { intent });
export const calculateKpi = (intent) => client.post("/calculate-kpi/", { intent });
export const resetSession = () => client.post("/reset-session/");
export const fetchSchema = () => client.get("/schema/");
