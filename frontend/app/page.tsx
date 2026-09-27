"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { Header, Disclaimer } from "@/components/Header";
import { KnowledgeBasePanel } from "@/components/KnowledgeBasePanel";
import { AnalysisInput } from "@/components/AnalysisInput";
import { AnalysisProgress } from "@/components/AnalysisProgress";
import { ReportView } from "@/components/report/ReportView";
import {
  ApiError,
  getAnalysisReport,
  getAnalysisStatus,
  getDocumentText,
  getDocuments,
  startAnalysis,
  uploadDocument,
} from "@/lib/api";
import type { AnalysisJobStatus, DocumentListResponse, FinalReport } from "@/types/api";

const POLL_INTERVAL_MS = 2000;

export default function Home() {
  const [docs, setDocs] = useState<DocumentListResponse | null>(null);
  const [docsLoading, setDocsLoading] = useState(true);
  const [docsError, setDocsError] = useState<string | null>(null);

  const [policyText, setPolicyText] = useState("");
  const [jobStatus, setJobStatus] = useState<AnalysisJobStatus | null>(null);
  const [report, setReport] = useState<FinalReport | null>(null);
  const [startError, setStartError] = useState<string | null>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const refreshDocs = useCallback(async () => {
    setDocsLoading(true);
    setDocsError(null);
    try {
      setDocs(await getDocuments());
    } catch (e) {
      setDocsError(e instanceof ApiError ? e.message : "Failed to load knowledge base.");
    } finally {
      setDocsLoading(false);
    }
  }, []);

  useEffect(() => {
    refreshDocs();
  }, [refreshDocs]);

  useEffect(() => {
    return () => {
      if (pollRef.current) clearInterval(pollRef.current);
    };
  }, []);

  async function handleStart(policyText: string) {
    setStartError(null);
    setReport(null);
    setJobStatus(null);
    try {
      const { job_id } = await startAnalysis(policyText);
      const poll = async () => {
        try {
          const status = await getAnalysisStatus(job_id);
          setJobStatus(status);
          if (status.stage === "complete") {
            if (pollRef.current) clearInterval(pollRef.current);
            const finalReport = await getAnalysisReport(job_id);
            setReport(finalReport);
          } else if (status.stage === "failed") {
            if (pollRef.current) clearInterval(pollRef.current);
          }
        } catch (e) {
          if (pollRef.current) clearInterval(pollRef.current);
          setStartError(e instanceof ApiError ? e.message : "Lost connection while polling analysis status.");
        }
      };
      poll();
      pollRef.current = setInterval(poll, POLL_INTERVAL_MS);
    } catch (e) {
      setStartError(e instanceof ApiError ? e.message : "Failed to start analysis.");
    }
  }

  async function handleUploadForAnalysis(file: File) {
    const { document } = await uploadDocument(file);
    const { text } = await getDocumentText(document);
    setPolicyText(text);
    refreshDocs();
  }

  const isRunning = !!jobStatus && jobStatus.stage !== "complete" && jobStatus.stage !== "failed";

  return (
    <div>
      <Header />
      <main className="mx-auto max-w-6xl space-y-6 px-6 py-8">
        <Disclaimer />

        <div className="grid gap-6 lg:grid-cols-[380px_1fr]">
          <div className="space-y-6">
            <KnowledgeBasePanel
              data={docs}
              loading={docsLoading}
              error={docsError}
              onRefresh={refreshDocs}
              onUseAsPolicyText={setPolicyText}
            />
          </div>

          <div className="space-y-6">
            <AnalysisInput
              text={policyText}
              onTextChange={setPolicyText}
              onStart={handleStart}
              onUploadPdf={handleUploadForAnalysis}
              disabled={isRunning}
            />
            {startError && (
              <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
                {startError}
              </div>
            )}
            {jobStatus && (jobStatus.stage !== "complete" || !report) && <AnalysisProgress status={jobStatus} />}
            {report && <ReportView report={report} />}
          </div>
        </div>
      </main>
    </div>
  );
}
