import { useEffect, useState } from "react";
import { fetchHomepageData, HomepageData } from "@/lib/api";
import { TopCard } from "@/components/TopCard";
import { WhatChangedToday } from "@/components/WhatChangedToday";
import { Signals } from "@/components/Signals";
import { Loader2, RefreshCwIcon, AlertCircleIcon } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";

export default function Home() {
  const [data, setData] = useState<HomepageData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await fetchHomepageData();
      setData(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load data");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  if (loading && !data) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background text-foreground">
        <div className="flex flex-col items-center space-y-4">
          <Loader2 className="h-12 w-12 animate-spin text-primary" />
          <p className="text-muted-foreground font-mono text-sm animate-pulse">CARREGANDO DADOS DE MERCADO...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background p-4">
        <Alert variant="destructive" className="max-w-md border-destructive/50 bg-destructive/10">
          <AlertCircleIcon className="h-4 w-4" />
          <AlertTitle>Erro de Conexão</AlertTitle>
          <AlertDescription className="mt-2">
            {error}
            <div className="mt-4">
              <Button onClick={loadData} variant="outline" className="w-full border-destructive/30 hover:bg-destructive/20">
                Tentar Novamente
              </Button>
            </div>
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background text-foreground font-sans selection:bg-chart-1 selection:text-black">
      {/* Hero Section with Abstract Background */}
      <div className="relative h-64 w-full overflow-hidden border-b border-border">
        <div className="absolute inset-0 bg-[url('/images/hero-background.jpg')] bg-cover bg-center opacity-40 mix-blend-luminosity" />
        <div className="absolute inset-0 bg-gradient-to-b from-transparent to-background" />
        
        <div className="container relative h-full flex flex-col justify-end pb-8">
          <div className="flex items-center space-x-4 mb-4">
            <div className="h-12 w-12 bg-foreground text-background flex items-center justify-center font-bold text-2xl tracking-tighter">
              FE
            </div>
            <div>
              <h1 className="text-4xl font-bold tracking-tight text-foreground">
                Fundamentos Econômicos
              </h1>
              <p className="text-muted-foreground font-mono text-sm mt-1">
                ANÁLISE MACROECONÔMICA E DE MERCADO
              </p>
            </div>
          </div>
        </div>
      </div>

      <main className="container py-8 space-y-8">
        {/* Meta Info Bar */}
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between border-b border-border pb-4 gap-4">
          <div className="flex items-center space-x-2 text-xs font-mono text-muted-foreground">
            <span className="inline-block w-2 h-2 bg-chart-1 rounded-full animate-pulse"></span>
            <span>SISTEMA OPERACIONAL</span>
            <span className="text-border">|</span>
            <span>V1.0.0</span>
          </div>
          
          <div className="flex items-center space-x-4">
            {data?.meta.stale && (
              <span className="text-xs font-mono text-destructive flex items-center px-2 py-1 bg-destructive/10 border border-destructive/20">
                <AlertCircleIcon className="w-3 h-3 mr-1" />
                DADOS PARCIALMENTE DESATUALIZADOS
              </span>
            )}
            <Button 
              variant="ghost" 
              size="sm" 
              onClick={loadData} 
              disabled={loading}
              className="text-xs font-mono hover:bg-secondary"
            >
              <RefreshCwIcon className={`w-3 h-3 mr-2 ${loading ? 'animate-spin' : ''}`} />
              ATUALIZAR
            </Button>
          </div>
        </div>

        {/* Top Cards Grid */}
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {data?.top_cards.map((card) => {
            const { key, ...rest } = card;
            return <TopCard key={key} {...rest} />;
          })}
        </div>

        {/* Main Content Grid */}
        <div className="grid gap-4 lg:grid-cols-3">
          {/* Left Column: What Changed */}
          <div className="lg:col-span-1">
            <WhatChangedToday items={data?.what_changed_today || []} />
          </div>

          {/* Right Column: Signals */}
          <div className="lg:col-span-2">
            <Signals signals={data?.signals || {}} />
          </div>
        </div>

        {/* Footer / Methodology */}
        <div className="mt-12 pt-8 border-t border-border text-center sm:text-left">
          <div className="grid gap-8 sm:grid-cols-2 lg:grid-cols-4 text-xs text-muted-foreground">
            <div>
              <h4 className="font-bold text-foreground mb-2 uppercase tracking-wider">Buffett + Graham</h4>
              <p>Foco em microeconomia e análise fundamentalista de empresas. Valor intrínseco e margem de segurança.</p>
            </div>
            <div>
              <h4 className="font-bold text-foreground mb-2 uppercase tracking-wider">Dalio + Volcker</h4>
              <p>Visão macroeconômica baseada em ciclos de dívida e política monetária. Entendimento da máquina econômica.</p>
            </div>
            <div>
              <h4 className="font-bold text-foreground mb-2 uppercase tracking-wider">Marks + Druckenmiller</h4>
              <p>Gerenciamento de risco e psicologia de mercado. Identificação de extremos e reversão à média.</p>
            </div>
            <div>
              <h4 className="font-bold text-foreground mb-2 uppercase tracking-wider">Metodologia</h4>
              <p>Dados oficiais (BCB, B3) processados sem viés editorial. Ceticismo em previsões e foco em dados históricos.</p>
            </div>
          </div>
          <div className="mt-8 text-center font-mono text-[10px] opacity-50">
            GENERATED AT: {data?.meta.generated_at} • MANUS AI SYSTEM
          </div>
        </div>
      </main>
    </div>
  );
}
