import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import { ActivityIcon, TrendingUpIcon, AlertTriangleIcon, BarChart3Icon } from "lucide-react";

interface SignalItem {
  key: string;
  label: string;
  value: number | null;
  unit: string;
  last_update: string;
}

interface SignalsProps {
  signals: Record<string, SignalItem>;
}

export function Signals({ signals }: SignalsProps) {
  const signalList = Object.values(signals);

  const getIcon = (key: string) => {
    if (key.includes("vol")) return <ActivityIcon className="h-4 w-4" />;
    if (key.includes("inflation")) return <TrendingUpIcon className="h-4 w-4" />;
    if (key.includes("rate")) return <BarChart3Icon className="h-4 w-4" />;
    return <AlertTriangleIcon className="h-4 w-4" />;
  };

  return (
    <Card className="border-border bg-card text-card-foreground h-full">
      <CardHeader>
        <CardTitle className="text-lg font-bold">Sinais de Mercado</CardTitle>
      </CardHeader>
      <CardContent className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {signalList.map((signal) => (
          <div 
            key={signal.key} 
            className="flex flex-col p-4 bg-background border border-border hover:border-primary/50 transition-all duration-200 relative overflow-hidden group"
          >
            <div className="absolute top-0 right-0 p-2 opacity-10 group-hover:opacity-20 transition-opacity">
              {getIcon(signal.key)}
            </div>
            
            <span className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-2">
              {signal.label}
            </span>
            
            <div className="mt-auto flex items-baseline space-x-2">
              <span className="text-2xl font-bold font-mono text-foreground">
                {signal.value !== null ? signal.value.toLocaleString("pt-BR", { maximumFractionDigits: 2 }) : "---"}
              </span>
              <span className="text-xs text-muted-foreground font-mono">{signal.unit}</span>
            </div>
            
            <div className="mt-2 h-1 w-full bg-secondary overflow-hidden">
              <div 
                className={cn(
                  "h-full transition-all duration-500",
                  signal.key.includes("vol") ? "bg-destructive" : "bg-chart-1"
                )}
                style={{ width: signal.value ? `${Math.min(Math.abs(signal.value) * 5, 100)}%` : '0%' }}
              />
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
