interface ValidationMetricProps {
  label: string;
  value: number;
  color: "blue" | "purple" | "indigo" | "green";
}

const colorClasses: Record<ValidationMetricProps["color"], string> = {
  blue: "text-blue-600",
  purple: "text-purple-600",
  indigo: "text-indigo-600",
  green: "text-green-600",
};

const bgColorClasses: Record<ValidationMetricProps["color"], string> = {
  blue: "bg-blue-500",
  purple: "bg-purple-500",
  indigo: "bg-indigo-500",
  green: "bg-green-500",
};

export function ValidationMetric({ label, value, color }: ValidationMetricProps) {
  return (
    <div className="text-center">
      <div className={`text-2xl font-bold ${colorClasses[color]}`}>{(value * 100).toFixed(1)}%</div>
      <div className="text-xs text-gray-500 mt-1">{label}</div>
      <div className="w-full bg-gray-200 rounded-full h-1.5 mt-2">
        <div
          className={`h-1.5 rounded-full ${bgColorClasses[color]} transition-all duration-500`}
          style={{ width: `${value * 100}%` }}
        />
      </div>
    </div>
  );
}
