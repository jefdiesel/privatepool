"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

export default function TermsOfService() {
  const router = useRouter();
  const [tosContent, setTosContent] = useState<string>("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/terms-of-service.html")
      .then((res) => res.text())
      .then((html) => {
        setTosContent(html);
        setLoading(false);
      })
      .catch(() => {
        setTosContent("<p>Terms of Service content could not be loaded.</p>");
        setLoading(false);
      });
  }, []);

  return (
    <div className="min-h-screen bg-black">
      {/* Header */}
      <div className="border-b border-red-500/20 bg-black/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <button
            onClick={() => router.push("/onboarding")}
            className="text-red-500 hover:text-red-400 transition-colors flex items-center gap-2"
          >
            <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M19 12H5M12 19l-7-7 7-7" />
            </svg>
            Back
          </button>
          <h1 className="text-red-500 font-bold text-lg">Terms of Service</h1>
          <div className="w-16" /> {/* Spacer for centering */}
        </div>
      </div>

      {/* Content */}
      <div className="container mx-auto px-4 py-8 max-w-3xl">
        <div className="border border-red-500/20 bg-slate-950/50 rounded-lg p-6 md:p-8">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <div className="w-8 h-8 border-2 border-red-500 border-t-transparent rounded-full animate-spin" />
            </div>
          ) : (
            <div
              className="prose prose-invert prose-red max-w-none
                         prose-headings:text-red-500 prose-headings:font-bold
                         prose-p:text-slate-300 prose-p:leading-relaxed
                         prose-a:text-red-400 prose-a:no-underline hover:prose-a:underline
                         prose-li:text-slate-300
                         prose-strong:text-white"
              dangerouslySetInnerHTML={{ __html: tosContent }}
            />
          )}
        </div>

        {/* Accept Button */}
        <div className="mt-8 text-center">
          <button
            onClick={() => router.push("/onboarding")}
            className="bg-red-500 hover:bg-red-600 text-white font-semibold px-8 py-3 rounded transition-colors"
          >
            Return to Accept Terms
          </button>
        </div>
      </div>
    </div>
  );
}
