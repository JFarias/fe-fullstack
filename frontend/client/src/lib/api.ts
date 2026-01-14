import { z } from "zod";

// Define Zod schemas for type safety based on the API contract

const TopCardSchema = z.object({
  key: z.string(),
  label: z.string(),
  value: z.number().nullable(),
  unit: z.string(),
  change_1d: z.number().nullable(),
  change_1d_unit: z.string(),
  last_update: z.string(),
});

const WhatChangedItemSchema = z.object({
  key: z.string(),
  label: z.string(),
  value: z.number().nullable(),
  unit: z.string(),
  extra: z.record(z.string(), z.any()).optional(),
  last_update: z.string(),
  period_label: z.string(),
});

const SignalItemSchema = z.object({
  key: z.string(),
  label: z.string(),
  value: z.number().nullable(),
  unit: z.string(),
  last_update: z.string(),
  source: z.string().optional(),
  method: z.string().optional(),
  components: z.record(z.string(), z.any()).optional(),
  cache: z.record(z.string(), z.any()).optional(),
  extra: z.record(z.string(), z.any()).optional(),
});

const SignalsSchema = z.object({
  real_rate_approx: SignalItemSchema,
  inflation_expectations_12m: SignalItemSchema,
  ibov_vol_20d_annualized: SignalItemSchema,
  usdbrl_vol_20d_annualized: SignalItemSchema,
  unemployment_latest: SignalItemSchema,
  gdp_latest: SignalItemSchema,
});

const MetaSchema = z.object({
  generated_at: z.string(),
  stale: z.boolean(),
  sources: z.record(z.string(), z.any()),
});

export const HomepageResponseSchema = z.object({
  top_cards: z.array(TopCardSchema),
  what_changed_today: z.array(WhatChangedItemSchema),
  signals: SignalsSchema,
  meta: MetaSchema,
});

export type HomepageData = z.infer<typeof HomepageResponseSchema>;

export async function fetchHomepageData(): Promise<HomepageData> {
  // In production, use the full URL from env var. In dev, use relative path for proxy.
  const baseUrl = import.meta.env.VITE_API_URL || "";
  const url = `${baseUrl}/api/homepage/v1`;
  
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Failed to fetch homepage data: ${response.statusText}`);
  }
  const data = await response.json();
  return HomepageResponseSchema.parse(data);
}
