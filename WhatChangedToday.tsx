import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import { ArrowRightIcon } from "lucide-react";

interface WhatChangedItem {
  key: string;
  label: string;
  value: number | null;
  unit: string;
  period_label: string;
}

interface WhatChangedTodayProps {
  items: WhatChangedItem[];
}

export function WhatChangedToday({ items }: WhatChangedTodayProps) {
  return (
    <Card className="border-border bg-card text-card-foreground h-full">
      <CardHeader>
        <CardTitle className="text-lg font-bold flex items-center">
          <span className="w-2 h-2 bg-chart-1 rounded-full mr-2 animate-pulse"></span>
          O Que Mudou Hoje
        </CardTitle>
      </CardHeader>
      <CardContent className="grid gap-4">
        {items.map((item) => {
          const isPositive = item.value !== null && item.value > 0;
          const isNegative = item.value !== null && item.value < 0;
          
          return (
            <div key={item.key} className="flex items-center justify-between p-3 bg-background/50 border border-border/50 hover:border-primary/20 transition-colors group">
              <div className="flex flex-col">
                <span className="text-sm font-medium text-muted-foreground group-hover:text-foreground transition-colors">
                  {item.label}
                </span>
                <span className="text-xs text-muted-foreground/70 uppercase tracking-wider">
                  {item.period_label}
                </span>
              </div>
              <div className="flex items-center space-x-2">
                <span 
                  className={cn(
                    "text-lg font-mono font-bold",
                    isPositive && "text-chart-1",
                    isNegative && "text-destructive",
                    !isPositive && !isNegative && "text-muted-foreground"
                  )}
                >
                  {item.value !== null ? (item.value > 0 ? "+" : "") + item.value.toLocaleString("pt-BR", { maximumFractionDigits: 2 }) : "---"}
                </span>
                <span className="text-xs text-muted-foreground font-mono">{item.unit}</span>
                <ArrowRightIcon className="h-4 w-4 text-muted-foreground/30 group-hover:text-primary transition-colors" />
              </div>
            </div>
          );
        })}
      </CardContent>
    </Card>
  );
}
