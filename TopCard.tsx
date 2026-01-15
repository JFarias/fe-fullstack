import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import { ArrowDownIcon, ArrowUpIcon, MinusIcon } from "lucide-react";

interface TopCardProps {
  label: string;
  value: number | null;
  unit: string;
  change_1d: number | null;
  change_1d_unit: string;
  last_update: string;
}

export function TopCard({ label, value, unit, change_1d, change_1d_unit }: TopCardProps) {
  const isPositive = change_1d !== null && change_1d > 0;
  const isNegative = change_1d !== null && change_1d < 0;
  const isNeutral = change_1d === 0 || change_1d === null;

  const formatValue = (val: number | null) => {
    if (val === null) return "---";
    // Format based on unit if needed, for now standard locale string
    return val.toLocaleString("pt-BR", { maximumFractionDigits: 2, minimumFractionDigits: 2 });
  };

  const formatChange = (val: number | null) => {
    if (val === null) return "---";
    return Math.abs(val).toLocaleString("pt-BR", { maximumFractionDigits: 2, minimumFractionDigits: 2 });
  };

  return (
    <Card className="border-border bg-card text-card-foreground shadow-sm">
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground uppercase tracking-wider">
          {label}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold font-mono tracking-tight">
          {formatValue(value)} <span className="text-sm font-normal text-muted-foreground ml-1">{unit}</span>
        </div>
        <div className="flex items-center mt-2 text-xs font-medium">
          {isPositive && <ArrowUpIcon className="mr-1 h-3 w-3 text-chart-1" />}
          {isNegative && <ArrowDownIcon className="mr-1 h-3 w-3 text-destructive" />}
          {isNeutral && <MinusIcon className="mr-1 h-3 w-3 text-muted-foreground" />}
          
          <span
            className={cn(
              isPositive && "text-chart-1",
              isNegative && "text-destructive",
              isNeutral && "text-muted-foreground"
            )}
          >
            {formatChange(change_1d)} {change_1d_unit}
          </span>
          <span className="text-muted-foreground ml-1">vs ontem</span>
        </div>
      </CardContent>
    </Card>
  );
}
