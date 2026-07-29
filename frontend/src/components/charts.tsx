"use client";

import ReactECharts from "echarts-for-react";
import { useTheme } from "next-themes";
import { useMemo } from "react";

function useChartColors() {
  const { resolvedTheme } = useTheme();
  const dark = resolvedTheme === "dark";
  return {
    text: dark ? "#e8f2ea" : "#0b1a12",
    muted: dark ? "#a8c0b2" : "#3a4a41",
    green: "#01411C",
    gold: dark ? "#c4a35a" : "#8a6d2f",
    cyan: dark ? "#2ec4c4" : "#0f6f6f",
    saffron: dark ? "#e08a2e" : "#b86a18",
    magenta: dark ? "#c23a6b" : "#a12e55",
    split: dark ? "rgba(196,163,90,0.15)" : "rgba(1,65,28,0.18)",
  };
}

export function YearChart({ data }: { data: { year: number; count: number }[] }) {
  const c = useChartColors();
  const option = useMemo(
    () => ({
      color: [c.green],
      tooltip: { trigger: "axis" },
      grid: { left: 40, right: 16, top: 24, bottom: 32 },
      xAxis: {
        type: "category",
        data: data.map((d) => d.year),
        axisLabel: { color: c.muted },
        axisLine: { lineStyle: { color: c.split } },
      },
      yAxis: {
        type: "value",
        minInterval: 1,
        axisLabel: { color: c.muted },
        splitLine: { lineStyle: { color: c.split } },
      },
      series: [
        {
          type: "line",
          smooth: true,
          areaStyle: { opacity: 0.18 },
          data: data.map((d) => d.count),
        },
      ],
    }),
    [data, c]
  );
  return <ReactECharts option={option} style={{ height: 280 }} opts={{ renderer: "svg" }} />;
}

export function ProvinceChart({ data }: { data: { province: string; count: number }[] }) {
  const c = useChartColors();
  const option = useMemo(
    () => ({
      color: [c.cyan],
      tooltip: { trigger: "axis" },
      grid: { left: 100, right: 16, top: 16, bottom: 24 },
      xAxis: {
        type: "value",
        axisLabel: { color: c.muted },
        splitLine: { lineStyle: { color: c.split } },
      },
      yAxis: {
        type: "category",
        data: data.map((d) => d.province).reverse(),
        axisLabel: { color: c.muted },
      },
      series: [
        {
          type: "bar",
          data: data.map((d) => d.count).reverse(),
          barWidth: 14,
          itemStyle: { borderRadius: [0, 6, 6, 0] },
        },
      ],
    }),
    [data, c]
  );
  return <ReactECharts option={option} style={{ height: 280 }} opts={{ renderer: "svg" }} />;
}

export function CategoryPie({ data }: { data: { category: string; count: number }[] }) {
  const c = useChartColors();
  const option = useMemo(
    () => ({
      color: [c.green, c.gold, c.cyan, c.saffron, c.magenta, "#4b7c59", "#7a5c2e"],
      tooltip: { trigger: "item" },
      series: [
        {
          type: "pie",
          radius: ["42%", "70%"],
          label: { color: c.text, formatter: "{b}" },
          data: data.map((d) => ({
            name: d.category.replace(/_/g, " "),
            value: d.count,
          })),
        },
      ],
    }),
    [data, c]
  );
  return <ReactECharts option={option} style={{ height: 300 }} opts={{ renderer: "svg" }} />;
}

export function StatusChart({ data }: { data: { status: string; count: number }[] }) {
  const c = useChartColors();
  const option = useMemo(
    () => ({
      color: [c.gold],
      tooltip: { trigger: "axis" },
      grid: { left: 120, right: 16, top: 16, bottom: 24 },
      xAxis: {
        type: "value",
        axisLabel: { color: c.muted },
        splitLine: { lineStyle: { color: c.split } },
      },
      yAxis: {
        type: "category",
        data: data.map((d) => d.status.replace(/_/g, " ")),
        axisLabel: { color: c.muted },
      },
      series: [{ type: "bar", data: data.map((d) => d.count), barWidth: 12 }],
    }),
    [data, c]
  );
  return <ReactECharts option={option} style={{ height: 320 }} opts={{ renderer: "svg" }} />;
}

export function SankeyChart({
  nodes,
  links,
}: {
  nodes: { name: string }[];
  links: { source: number; target: number; value: number }[];
}) {
  const c = useChartColors();
  const option = useMemo(
    () => ({
      tooltip: { trigger: "item" },
      series: [
        {
          type: "sankey",
          data: nodes,
          links: links.map((l) => ({
            source: nodes[l.source]?.name,
            target: nodes[l.target]?.name,
            value: l.value,
          })),
          lineStyle: { color: "gradient", opacity: 0.35 },
          itemStyle: { borderWidth: 0 },
          label: { color: c.text, fontSize: 11 },
        },
      ],
    }),
    [nodes, links, c]
  );
  if (!nodes.length) {
    return <p className="text-sm text-[var(--muted)]">No documented amount flows available.</p>;
  }
  return <ReactECharts option={option} style={{ height: 420 }} opts={{ renderer: "svg" }} />;
}
